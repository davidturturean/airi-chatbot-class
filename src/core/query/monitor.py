import google.generativeai as genai
import logging
import json
import re

from ...config.patterns import pattern_matcher
from ...config.prompts import prompt_formatter
from ...config.domains import domain_classifier
from ...config.settings import settings
from ...config.logging import get_logger
from ..models.gemini import GeminiModel

logger = get_logger(__name__)

class Monitor:
    """
    Monitor class to filter messages and determine inquiry type.
    Acts as the first step in the processing pipeline with model chain fallback.
    """
    
    def __init__(self, api_key, model_name=None):
        """Initialize the Monitor with API access and model chain fallback."""
        self.api_key = api_key
        self.model_name = model_name or settings.MONITOR_MODEL_NAME
        
        # Initialize Gemini model with fallback chain
        self.gemini_model = GeminiModel(
            api_key=api_key,
            model_name=self.model_name,
            use_fallback=True  # Enable model chain fallback
        )
        
        # Legacy client for backward compatibility
        genai.configure(api_key=api_key)
        self.client = genai
        
        # Configuration components
        self.pattern_matcher = pattern_matcher
        self.prompt_formatter = prompt_formatter
        self.domain_classifier = domain_classifier
        
        logger.info(f"Monitor initialized with model chain fallback enabled")
    
    def determine_inquiry_type(self, user_input):
        """
        Determine the type of inquiry and whether it's an override attempt.
        
        Args:
            user_input (str): The user's message
            
        Returns:
            dict: Contains inquiry_type, override_attempt, and primary_domain
        """
        # Try model-based classification first for better semantic understanding
        if settings.MONITOR_ENABLE_MODEL_BASED:
            try:
                # Check if we should skip LLM due to recent quota failures
                if hasattr(self.gemini_model, 'model_pool') and self.gemini_model.model_pool:
                    # Check if all models are in cooldown
                    available_models = [m for m in self.gemini_model.model_pool.model_chain 
                                      if self.gemini_model.model_pool._is_model_available(m)]
                    
                    if not available_models:
                        logger.warning("All models in cooldown, skipping LLM classification")
                        raise Exception("All models in cooldown")
                
                # Create conversation history using prompt formatter
                conversation = self.prompt_formatter.build_conversation_history(user_input)
                
                # Generate response using model chain fallback
                logger.info(f"Attempting LLM classification with model chain fallback...")
                
                # Use the enhanced Gemini model with fallback
                logger.info(f"🎯 Monitor calling gemini_model.generate()")
                response_text = self.gemini_model.generate(
                    self.prompt_formatter.get_classification_request(),
                    history=conversation
                )
                logger.info(f"🎯 Monitor received response: {response_text[:100]}...")
                
                # Check if model pool returned an error message instead of JSON
                if response_text.startswith("I encountered an error while generating a response"):
                    logger.warning("Model pool failed completely, falling back to rule-based classification")
                    raise Exception("Model pool failed completely")
            
                # Extract JSON from response
                try:
                    # Find JSON in the response if it's embedded in other text
                    response_text = response_text.strip()
                    if response_text.startswith('```json'):
                        response_text = response_text.replace('```json', '', 1)
                        response_text = response_text.replace('```', '', 1)
                
                    logger.info(f"🎯 Parsing JSON response: {response_text}")
                    result = json.loads(response_text.strip())
                    logger.info(f"🎯 Parsed JSON result: {result}")
                
                    # Validate result structure using domain classifier
                    if not self.domain_classifier.validate_classification_result(result):
                        logger.warning(f"🎯 Invalid monitor response format - validation failed for: {result}")
                        return self._default_result()
                    
                    logger.info(f"🎯 Validation passed, returning: {result}")
                    return result
                    
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse monitor response: {response_text}")
                    return self._default_result()
                    
            except Exception as e:
                error_str = str(e)
                logger.error(f"Error in monitor: {error_str}")
                
                # Check if this is a quota error
                if "429" in error_str or "quota" in error_str.lower():
                    logger.warning(f"Model chain failed with quota error, falling back to rule-based classification")
                    # Try rule-based classification as fallback
                    rule_result = self._rule_based_classification(user_input)
                    if rule_result:
                        return rule_result
                
                # Always try rule-based classification before giving up
                logger.warning(f"Model chain failed completely, trying rule-based classification")
                rule_result = self._rule_based_classification(user_input)
                if rule_result:
                    return rule_result
                
                return self._default_result()
        
        # Fall back to rule-based classification if LLM failed
        if settings.MONITOR_ENABLE_RULE_BASED:
            logger.info(f"🎯 LLM failed, trying rule-based classification as fallback")
            rule_result = self._rule_based_classification(user_input)
            if rule_result:
                logger.info(f"🎯 Rule-based classification succeeded: {rule_result}")
                return rule_result
            else:
                logger.info(f"🎯 Rule-based classification also failed")
        
        # If both LLM and rule-based are disabled or failed, return default
        logger.warning("Both LLM and rule-based classification failed or are disabled")
        return self._default_result()
    
    def _rule_based_classification(self, user_input):
        """
        Perform a simple rule-based classification before using the model.
        This is faster and can handle common cases.
        
        Args:
            user_input (str): The user's message
            
        Returns:
            dict or None: Classification result or None if rules don't apply
        """
        input_lower = user_input.lower()
        
        # Check for override attempts
        if self.pattern_matcher.matches_override_patterns(input_lower):
            return {
                "inquiry_type": "OUT_OF_SCOPE",
                "override_attempt": True,
                "primary_domain": "OTHER"
            }
        
        # Check for employment-related queries
        if (self.pattern_matcher.matches_employment_patterns(input_lower) and 
            self.pattern_matcher.has_ai_context(input_lower)):
            return {
                "inquiry_type": "EMPLOYMENT_RISK",
                "override_attempt": False,
                "primary_domain": "SOCIOECONOMIC"
            }
            
        # Check for specific risk inquiries
        if (self.pattern_matcher.matches_risk_patterns(input_lower) and 
            self.pattern_matcher.has_ai_context(input_lower)):
            # Try to determine domain using keyword matching
            domain = self.domain_classifier.classify_domain_by_keywords(input_lower)
            return {
                "inquiry_type": "SPECIFIC_RISK",
                "override_attempt": False,
                "primary_domain": domain.upper()
            }
        
        # Enhanced rule-based domain detection for common cases
        import re
        bias_keywords = ['bias', 'discrimination', 'unfair', 'prejudice', 'racial', 'gender', 'stereotyp']
        safety_keywords = ['safety', 'danger', 'harm', 'risk', 'accident', 'security']
        privacy_keywords = ['privacy', 'data', 'surveillance', 'monitoring', 'personal information']
        socioeconomic_keywords = ['employment', 'job', 'economic', 'unemployment', 'automation']  # Removed "work" to prevent false positives
        governance_keywords = ['regulation', 'policy', 'governance', 'legal', 'law', 'compliance', 'oversight']
        technical_keywords = ['algorithm', 'performance', 'accuracy', 'reliability', 'technical', 'robust', 'network', 'networks', 'neural', 'input', 'inputs']
        
        # Helper function to check word boundaries
        def has_keyword(keywords, text):
            return any(re.search(r'\b' + re.escape(keyword) + r'\b', text) for keyword in keywords)
        
        if has_keyword(bias_keywords, input_lower):
            return {
                "inquiry_type": "SPECIFIC_RISK",
                "override_attempt": False,
                "primary_domain": "BIAS",
                "confidence": "MEDIUM",
                "reasoning": "Detected bias-related keywords in rule-based classification"
            }
        
        if has_keyword(safety_keywords, input_lower):
            return {
                "inquiry_type": "SPECIFIC_RISK", 
                "override_attempt": False,
                "primary_domain": "SAFETY",
                "confidence": "MEDIUM",
                "reasoning": "Detected safety-related keywords in rule-based classification"
            }
        
        if has_keyword(privacy_keywords, input_lower):
            return {
                "inquiry_type": "SPECIFIC_RISK",
                "override_attempt": False,
                "primary_domain": "PRIVACY",
                "confidence": "MEDIUM", 
                "reasoning": "Detected privacy-related keywords in rule-based classification"
            }
        
        if has_keyword(socioeconomic_keywords, input_lower):
            return {
                "inquiry_type": "SPECIFIC_RISK",
                "override_attempt": False,
                "primary_domain": "SOCIOECONOMIC",
                "confidence": "MEDIUM",
                "reasoning": "Detected socioeconomic-related keywords in rule-based classification"
            }
        
        if has_keyword(governance_keywords, input_lower):
            return {
                "inquiry_type": "SPECIFIC_RISK",
                "override_attempt": False,
                "primary_domain": "GOVERNANCE",
                "confidence": "MEDIUM",
                "reasoning": "Detected governance-related keywords in rule-based classification"
            }
        
        if has_keyword(technical_keywords, input_lower):
            return {
                "inquiry_type": "SPECIFIC_RISK",
                "override_attempt": False,
                "primary_domain": "TECHNICAL",
                "confidence": "MEDIUM",
                "reasoning": "Detected technical-related keywords in rule-based classification"
            }
            
        # General repository questions
        if self.pattern_matcher.matches_repository_patterns(input_lower):
            return {
                "inquiry_type": "GENERAL",
                "override_attempt": False,
                "primary_domain": "OTHER"
            }
        
        # If no rules match, return None to use model classification
        return None
    
    def _default_result(self):
        """Return a default result when processing fails."""
        return self.domain_classifier.get_default_classification()