"""
Self-validation chain for response quality assessment.
Ensures responses are accurate, relevant, and appropriate.
"""
import re
import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from langchain.docstore.document import Document

from ...config.logging import get_logger
from ...config.settings import settings

logger = get_logger(__name__)

class ValidationResult(Enum):
    """Results of validation checks."""
    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"

class ValidationCategory(Enum):
    """Categories of validation checks."""
    FACTUAL_ACCURACY = "factual_accuracy"
    RELEVANCE = "relevance"
    COMPLETENESS = "completeness"
    APPROPRIATENESS = "appropriateness"
    CITATION_QUALITY = "citation_quality"
    COHERENCE = "coherence"

@dataclass
class ValidationCheck:
    """Individual validation check result."""
    category: ValidationCategory
    result: ValidationResult
    score: float  # 0.0 to 1.0
    message: str
    details: Optional[str] = None

@dataclass
class ResponseValidation:
    """Complete validation results for a response."""
    overall_score: float
    overall_result: ValidationResult
    checks: List[ValidationCheck]
    recommendations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "overall_score": self.overall_score,
            "overall_result": self.overall_result.value,
            "checks": [
                {
                    "category": check.category.value,
                    "result": check.result.value,
                    "score": check.score,
                    "message": check.message,
                    "details": check.details
                }
                for check in self.checks
            ],
            "recommendations": self.recommendations
        }

class ResponseValidator:
    """Validates response quality using multiple criteria."""
    
    def __init__(self):
        self._init_validation_patterns()
        self._init_quality_thresholds()
    
    def _init_validation_patterns(self):
        """Initialize patterns for validation checks."""
        
        # Inappropriate content patterns
        self.inappropriate_patterns = [
            r'i don\'t know',
            r'i\'m not sure',
            r'i cannot provide',
            r'i\'m sorry, but',
            r'unfortunately, i',
            r'this is outside',
            r'beyond my scope'
        ]
        
        # Low-confidence language patterns
        self.low_confidence_patterns = [
            r'might',
            r'possibly',
            r'perhaps',
            r'maybe',
            r'could be',
            r'it\'s possible',
            r'uncertain'
        ]
        
        # Citation patterns
        self.citation_patterns = [
            r'RID-\d{5}',  # RID citations
            r'\[Source \d+\]',  # Legacy citations
            r'according to',
            r'based on',
            r'the repository'
        ]
        
        # Factual claim patterns
        self.factual_claim_patterns = [
            r'\d+%',  # Percentages
            r'\d+\.\d+%',  # Decimal percentages
            r'studies show',
            r'research indicates',
            r'data reveals',
            r'evidence suggests'
        ]
    
    def _init_quality_thresholds(self):
        """Initialize quality thresholds for validation."""
        self.thresholds = {
            ValidationCategory.FACTUAL_ACCURACY: 0.7,
            ValidationCategory.RELEVANCE: 0.8,
            ValidationCategory.COMPLETENESS: 0.6,
            ValidationCategory.APPROPRIATENESS: 0.9,
            ValidationCategory.CITATION_QUALITY: 0.7,
            ValidationCategory.COHERENCE: 0.8
        }
        
        self.overall_pass_threshold = 0.75
        self.overall_warning_threshold = 0.60
    
    def validate_response(self, 
                         response: str, 
                         query: str,
                         retrieved_documents: List[Document],
                         domain: str = "general") -> ResponseValidation:
        """
        Perform comprehensive validation with three-signal scoring.
        
        Args:
            response: The generated response
            query: Original user query
            retrieved_documents: Documents used for generation
            domain: Domain context
            
        Returns:
            Complete validation results with three-signal analysis
        """
        checks = []
        
        # Run all validation checks
        accuracy_check = self._check_factual_accuracy(response, retrieved_documents)
        relevance_check = self._check_relevance(response, query, domain)
        completeness_check = self._check_completeness(response, query)
        appropriateness_check = self._check_appropriateness(response)
        citation_check = self._check_citation_quality(response, retrieved_documents)
        coherence_check = self._check_coherence(response)
        
        checks.extend([accuracy_check, relevance_check, completeness_check, 
                      appropriateness_check, citation_check, coherence_check])
        
        # Three-signal scoring
        accuracy_score = accuracy_check.score
        coverage_score = (completeness_check.score + relevance_check.score) / 2
        style_score = (appropriateness_check.score + coherence_check.score) / 2
        
        # Calculate weighted overall score
        overall_score = (accuracy_score * 0.4 + coverage_score * 0.4 + style_score * 0.2)
        
        # Determine overall result with three-signal logic
        if overall_score >= self.overall_pass_threshold:
            overall_result = ValidationResult.PASS
        elif overall_score >= self.overall_warning_threshold:
            overall_result = ValidationResult.WARNING
        else:
            overall_result = ValidationResult.FAIL
        
        # Special case: High accuracy but low coverage suggests revision opportunity
        if accuracy_score >= 0.75 and coverage_score < 0.5:
            overall_result = ValidationResult.WARNING  # Upgrade from FAIL to WARNING
            logger.info(f"High accuracy ({accuracy_score:.2f}) but low coverage ({coverage_score:.2f}) - revision candidate")
        
        # Log three-signal breakdown
        logger.info(f"Three-signal scores - Accuracy: {accuracy_score:.2f}, Coverage: {coverage_score:.2f}, Style: {style_score:.2f}")
        
        # Generate recommendations
        recommendations = self._generate_recommendations(checks, overall_score)
        
        return ResponseValidation(
            overall_score=overall_score,
            overall_result=overall_result,
            checks=checks,
            recommendations=recommendations
        )
    
    def _check_factual_accuracy(self, response: str, documents: List[Document]) -> ValidationCheck:
        """Check if response appears factually accurate based on source documents."""
        
        score = 0.8  # Default good score
        message = "Factual accuracy appears acceptable"
        result = ValidationResult.PASS
        details = None
        
        try:
            # Check for unsupported factual claims
            factual_claims = []
            for pattern in self.factual_claim_patterns:
                matches = re.findall(pattern, response.lower())
                factual_claims.extend(matches)
            
            if factual_claims:
                # Verify claims against source documents
                doc_text = " ".join([doc.page_content.lower() for doc in documents])
                
                unsupported_claims = 0
                for claim in factual_claims:
                    if claim not in doc_text:
                        unsupported_claims += 1
                
                if unsupported_claims > 0:
                    accuracy_ratio = 1.0 - (unsupported_claims / len(factual_claims))
                    score = max(0.3, accuracy_ratio)
                    
                    if score < 0.6:
                        result = ValidationResult.FAIL
                        message = f"Multiple unsupported factual claims detected"
                        details = f"{unsupported_claims}/{len(factual_claims)} claims not found in sources"
                    else:
                        result = ValidationResult.WARNING
                        message = "Some factual claims may not be well-supported"
            
            # Check for hedging language that might indicate uncertainty
            hedging_count = sum(1 for pattern in self.low_confidence_patterns 
                              if re.search(pattern, response.lower()))
            
            if hedging_count > 3:
                score *= 0.9  # Slight penalty for excessive hedging
                
        except Exception as e:
            logger.error(f"Error in factual accuracy check: {str(e)}")
            score = 0.7
            result = ValidationResult.WARNING
            message = "Could not fully validate factual accuracy"
        
        return ValidationCheck(
            category=ValidationCategory.FACTUAL_ACCURACY,
            result=result,
            score=score,
            message=message,
            details=details
        )
    
    def _check_relevance(self, response: str, query: str, domain: str) -> ValidationCheck:
        """Check if response is relevant to the user's query."""
        
        score = 0.8
        message = "Response appears relevant to query"
        result = ValidationResult.PASS
        
        try:
            # Check keyword overlap
            query_words = set(query.lower().split())
            response_words = set(response.lower().split())
            
            # Remove common stop words
            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
            query_words -= stop_words
            response_words -= stop_words
            
            if query_words:
                overlap_ratio = len(query_words.intersection(response_words)) / len(query_words)
                score = max(0.4, overlap_ratio + 0.3)  # Base score + overlap bonus
                
                if overlap_ratio < 0.3:
                    result = ValidationResult.WARNING
                    message = "Response may not fully address the query"
                elif overlap_ratio < 0.1:
                    result = ValidationResult.FAIL
                    message = "Response appears unrelated to query"
            
            # Domain relevance check
            if domain != "general" and domain != "other":
                domain_keywords = {
                    'socioeconomic': ['employment', 'job', 'work', 'economic', 'wage', 'labor'],
                    'safety': ['safety', 'risk', 'danger', 'harm', 'accident', 'failure'],
                    'privacy': ['privacy', 'data', 'personal', 'surveillance', 'information'],
                    'bias': ['bias', 'discrimination', 'fairness', 'equity', 'prejudice']
                }
                
                if domain in domain_keywords:
                    domain_words = set(domain_keywords[domain])
                    domain_overlap = len(domain_words.intersection(response_words))
                    
                    if domain_overlap == 0:
                        score *= 0.8  # Penalty for missing domain context
                        message = f"Response may not address {domain} aspects"
                
        except Exception as e:
            logger.error(f"Error in relevance check: {str(e)}")
            score = 0.7
            result = ValidationResult.WARNING
            message = "Could not fully validate relevance"
        
        return ValidationCheck(
            category=ValidationCategory.RELEVANCE,
            result=result,
            score=score,
            message=message
        )
    
    def _check_completeness(self, response: str, query: str) -> ValidationCheck:
        """Check if response adequately addresses the query."""
        
        score = 0.7
        message = "Response appears reasonably complete"
        result = ValidationResult.PASS
        
        try:
            # Check response length
            response_length = len(response.strip())
            
            if response_length < 100:
                score = 0.4
                result = ValidationResult.WARNING
                message = "Response may be too brief"
            elif response_length < 50:
                score = 0.2
                result = ValidationResult.FAIL
                message = "Response is too short to be complete"
            elif response_length > 2000:
                score = 0.8
                message = "Response is comprehensive but may be too long"
            
            # Check for question words in query that should be addressed
            question_words = ['how', 'what', 'why', 'when', 'where', 'which', 'who']
            query_questions = [word for word in question_words if word in query.lower()]
            
            if query_questions:
                # Very basic check - could be enhanced with NLP
                addressed_count = 0
                for q_word in query_questions:
                    if q_word in response.lower() or any(indicator in response.lower() 
                                                       for indicator in ['by', 'through', 'because', 'since']):
                        addressed_count += 1
                
                if addressed_count == 0 and len(query_questions) > 0:
                    score *= 0.8
                    message = "Response may not fully answer the question"
                    
        except Exception as e:
            logger.error(f"Error in completeness check: {str(e)}")
            score = 0.6
            result = ValidationResult.WARNING
            message = "Could not fully validate completeness"
        
        return ValidationCheck(
            category=ValidationCategory.COMPLETENESS,
            result=result,
            score=score,
            message=message
        )
    
    def _check_appropriateness(self, response: str) -> ValidationCheck:
        """Check if response is appropriate and professional."""
        
        score = 0.9
        message = "Response is appropriate"
        result = ValidationResult.PASS
        
        try:
            response_lower = response.lower()
            
            # Check for inappropriate deflection
            inappropriate_count = sum(1 for pattern in self.inappropriate_patterns 
                                    if re.search(pattern, response_lower))
            
            if inappropriate_count > 0:
                score = 0.3
                result = ValidationResult.FAIL
                message = "Response contains inappropriate deflection"
            
            # Check for excessive disclaimers
            disclaimer_patterns = [
                r'i am not',
                r'please consult',
                r'seek professional',
                r'this is not advice'
            ]
            
            disclaimer_count = sum(1 for pattern in disclaimer_patterns 
                                 if re.search(pattern, response_lower))
            
            if disclaimer_count > 2:
                score *= 0.8
                message = "Response contains excessive disclaimers"
            
            # Check for confident, helpful tone
            if any(phrase in response_lower for phrase in ['the repository documents', 'based on', 'according to']):
                score = min(1.0, score + 0.1)  # Bonus for citing sources
                
        except Exception as e:
            logger.error(f"Error in appropriateness check: {str(e)}")
            score = 0.8
            result = ValidationResult.WARNING
            message = "Could not fully validate appropriateness"
        
        return ValidationCheck(
            category=ValidationCategory.APPROPRIATENESS,
            result=result,
            score=score,
            message=message
        )
    
    def _check_citation_quality(self, response: str, documents: List[Document]) -> ValidationCheck:
        """Check quality and appropriateness of citations."""
        
        score = 0.6
        message = "Citation quality is acceptable"
        result = ValidationResult.PASS
        
        try:
            # Count citations in response
            rid_citations = len(re.findall(r'RID-\d{5}', response))
            legacy_citations = len(re.findall(r'\[Source \d+\]', response))
            total_citations = rid_citations + legacy_citations
            
            # Check if response has documents but no citations
            if len(documents) > 0:
                if total_citations == 0:
                    score = 0.3
                    result = ValidationResult.WARNING
                    message = "Response lacks proper citations despite having source documents"
                elif rid_citations > 0:
                    score = 0.9  # Bonus for using RID format
                    message = "Good citation quality with RID format"
                else:
                    score = 0.7
                    message = "Citations present but could use RID format"
            else:
                if total_citations > 0:
                    score = 0.4
                    result = ValidationResult.WARNING
                    message = "Response has citations but no source documents provided"
            
            # Check for citation density (not too many, not too few)
            response_length = len(response.split())
            if response_length > 0 and total_citations > 0:
                citation_density = total_citations / (response_length / 100)  # Per 100 words
                
                if citation_density > 5:  # Too many citations
                    score *= 0.9
                    message = "Response may have excessive citations"
                elif citation_density < 0.5 and len(documents) > 2:  # Too few citations
                    score *= 0.8
                    message = "Response could benefit from more citations"
                    
        except Exception as e:
            logger.error(f"Error in citation quality check: {str(e)}")
            score = 0.6
            result = ValidationResult.WARNING
            message = "Could not fully validate citation quality"
        
        return ValidationCheck(
            category=ValidationCategory.CITATION_QUALITY,
            result=result,
            score=score,
            message=message
        )
    
    def _check_coherence(self, response: str) -> ValidationCheck:
        """Check if response is coherent and well-structured."""
        
        score = 0.8
        message = "Response is coherent"
        result = ValidationResult.PASS
        
        try:
            # Basic coherence checks
            sentences = [s.strip() for s in response.split('.') if s.strip()]
            
            if len(sentences) < 2:
                score = 0.6
                message = "Response may be too brief for coherence assessment"
            
            # Check for transition words (basic coherence indicator)
            transition_words = [
                'however', 'therefore', 'furthermore', 'additionally', 'moreover',
                'consequently', 'thus', 'meanwhile', 'similarly', 'in contrast'
            ]
            
            transition_count = sum(1 for word in transition_words 
                                 if word in response.lower())
            
            if len(sentences) > 3 and transition_count == 0:
                score *= 0.9
                message = "Response could benefit from better transitions"
            
            # Check for repetitive content
            word_counts = {}
            words = response.lower().split()
            for word in words:
                if len(word) > 4:  # Only count significant words
                    word_counts[word] = word_counts.get(word, 0) + 1
            
            max_repetitions = max(word_counts.values()) if word_counts else 0
            if max_repetitions > len(words) * 0.1:  # More than 10% repetition
                score *= 0.8
                message = "Response contains repetitive content"
                
        except Exception as e:
            logger.error(f"Error in coherence check: {str(e)}")
            score = 0.7
            result = ValidationResult.WARNING
            message = "Could not fully validate coherence"
        
        return ValidationCheck(
            category=ValidationCategory.COHERENCE,
            result=result,
            score=score,
            message=message
        )
    
    def _generate_recommendations(self, checks: List[ValidationCheck], overall_score: float) -> List[str]:
        """Generate recommendations based on validation results."""
        
        recommendations = []
        
        # Check for specific issues and suggest improvements
        for check in checks:
            if check.result == ValidationResult.FAIL:
                if check.category == ValidationCategory.FACTUAL_ACCURACY:
                    recommendations.append("Verify factual claims against source documents")
                elif check.category == ValidationCategory.RELEVANCE:
                    recommendations.append("Ensure response directly addresses user query")
                elif check.category == ValidationCategory.COMPLETENESS:
                    recommendations.append("Provide more comprehensive information")
                elif check.category == ValidationCategory.APPROPRIATENESS:
                    recommendations.append("Use more confident, helpful language")
                elif check.category == ValidationCategory.CITATION_QUALITY:
                    recommendations.append("Add proper RID citations for claims")
                elif check.category == ValidationCategory.COHERENCE:
                    recommendations.append("Improve response structure and flow")
            
            elif check.result == ValidationResult.WARNING:
                if check.category == ValidationCategory.CITATION_QUALITY:
                    recommendations.append("Consider using RID citation format")
                elif check.category == ValidationCategory.COMPLETENESS:
                    recommendations.append("Response could be more detailed")
        
        # Overall recommendations
        if overall_score < 0.7:
            recommendations.append("Response needs significant improvement before use")
        elif overall_score < 0.8:
            recommendations.append("Response is acceptable but could be enhanced")
        
        if not recommendations:
            recommendations.append("Response quality is good")
        
        return recommendations

class SelfValidationChain:
    """Manages the self-validation process for responses."""
    
    def __init__(self, enable_validation: bool = True):
        self.enable_validation = enable_validation
        self.validator = ResponseValidator()
        self.validation_history = []
    
    def validate_and_improve(self, 
                           response: str,
                           query: str, 
                           documents: List[Document],
                           domain: str = "general",
                           max_iterations: int = 2) -> Tuple[str, ResponseValidation]:
        """
        Validate a response and suggest improvements.
        
        Args:
            response: Generated response
            query: Original query
            documents: Source documents
            domain: Domain context
            max_iterations: Maximum improvement iterations
            
        Returns:
            Tuple of (final_response, validation_results)
        """
        if not self.enable_validation:
            # Return original response with basic validation
            basic_validation = ResponseValidation(
                overall_score=0.8,
                overall_result=ValidationResult.PASS,
                checks=[],
                recommendations=["Validation disabled"]
            )
            return response, basic_validation
        
        current_response = response
        response_history = [response]  # Track response history to detect cycles
        
        for iteration in range(max_iterations):
            # Validate current response
            validation = self.validator.validate_response(
                current_response, query, documents, domain
            )
            
            # Store validation history
            self.validation_history.append({
                'iteration': iteration,
                'validation': validation,
                'response_length': len(current_response)
            })
            
            # If validation passes or this is the last iteration, return
            if (validation.overall_result == ValidationResult.PASS or 
                iteration == max_iterations - 1):
                return current_response, validation
            
            # Check if response is a revision candidate (high accuracy but low coverage)
            accuracy_score = next((c.score for c in validation.checks if c.category == ValidationCategory.FACTUAL_ACCURACY), 0.0)
            coverage_checks = [c for c in validation.checks if c.category in [ValidationCategory.COMPLETENESS, ValidationCategory.RELEVANCE]]
            coverage_score = sum(c.score for c in coverage_checks) / len(coverage_checks) if coverage_checks else 0.0
            
            if accuracy_score >= 0.75 and coverage_score < 0.5:
                logger.info(f"Attempting revision: high accuracy ({accuracy_score:.2f}) but low coverage ({coverage_score:.2f})")
                revised_response = self._generate_revision_suggestion(current_response, query, documents, validation)
                if revised_response and revised_response != current_response:
                    # Check for cycles - compare with previous responses
                    if self._is_response_cycle(revised_response, response_history):
                        logger.warning(f"Detected revision cycle - stopping iteration to prevent infinite loop")
                        break
                    
                    current_response = revised_response
                    response_history.append(revised_response)
                    logger.info(f"Generated revision, continuing validation...")
                    continue
            
            # If no revision or revision failed, break
            logger.info(f"Validation iteration {iteration + 1}: Score {validation.overall_score:.2f}")
            break
        
        return current_response, validation
    
    def _is_response_cycle(self, new_response: str, response_history: List[str]) -> bool:
        """
        Check if the new response creates a cycle with previous responses.
        Uses semantic similarity and content fingerprinting to detect near-duplicate responses.
        """
        if not response_history:
            return False
        
        try:
            # Normalize responses for comparison
            new_normalized = self._normalize_response_for_comparison(new_response)
            
            for i, previous_response in enumerate(response_history):
                prev_normalized = self._normalize_response_for_comparison(previous_response)
                
                # Check for exact matches after normalization
                if new_normalized == prev_normalized:
                    logger.warning(f"Exact response cycle detected with history item {i}")
                    return True
                
                # Check semantic similarity using multiple approaches
                similarity_score = self._calculate_response_similarity(new_normalized, prev_normalized)
                
                # Configure similarity threshold based on response length
                if len(new_normalized) < 100:  # Short responses
                    similarity_threshold = 0.95
                elif len(new_normalized) < 500:  # Medium responses  
                    similarity_threshold = 0.85
                else:  # Long responses
                    similarity_threshold = 0.80
                
                if similarity_score > similarity_threshold:
                    logger.warning(f"High similarity cycle detected with history item {i} "
                                 f"(score: {similarity_score:.3f}, threshold: {similarity_threshold})")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error in cycle detection: {e}")
            # Fall back to simple comparison to avoid breaking validation
            return any(new_response.strip() == prev.strip() for prev in response_history)
    
    def _normalize_response_for_comparison(self, response: str) -> str:
        """Normalize response text for better cycle detection."""
        import re
        
        # Remove extra whitespace and normalize
        normalized = ' '.join(response.split())
        
        # Remove markdown formatting that might vary
        normalized = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', normalized)  # Remove links
        normalized = re.sub(r'\*\*([^*]+)\*\*', r'\1', normalized)      # Remove bold
        normalized = re.sub(r'\*([^*]+)\*', r'\1', normalized)          # Remove italic
        
        # Remove citation patterns that might vary
        normalized = re.sub(r'RID-\d+', 'RID-XXX', normalized)          # Normalize RID citations
        
        return normalized.lower().strip()
    
    def _calculate_response_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two responses using multiple methods."""
        try:
            # Method 1: Jaccard similarity for word overlap
            words1 = set(text1.split())
            words2 = set(text2.split())
            
            if not words1 or not words2:
                jaccard_sim = 0.0
            else:
                intersection = len(words1.intersection(words2))
                union = len(words1.union(words2))
                jaccard_sim = intersection / union if union > 0 else 0.0
            
            # Method 2: Character n-gram similarity for structural similarity
            def get_ngrams(text, n=3):
                return set(text[i:i+n] for i in range(len(text) - n + 1))
            
            ngrams1 = get_ngrams(text1)
            ngrams2 = get_ngrams(text2)
            
            if not ngrams1 or not ngrams2:
                ngram_sim = 0.0
            else:
                ngram_intersection = len(ngrams1.intersection(ngrams2))
                ngram_union = len(ngrams1.union(ngrams2))
                ngram_sim = ngram_intersection / ngram_union if ngram_union > 0 else 0.0
            
            # Method 3: Length-normalized Levenshtein distance
            def levenshtein_similarity(s1, s2):
                if len(s1) == 0 or len(s2) == 0:
                    return 0.0
                
                # Simple Levenshtein distance calculation
                matrix = [[0] * (len(s2) + 1) for _ in range(len(s1) + 1)]
                
                for i in range(len(s1) + 1):
                    matrix[i][0] = i
                for j in range(len(s2) + 1):
                    matrix[0][j] = j
                
                for i in range(1, len(s1) + 1):
                    for j in range(1, len(s2) + 1):
                        cost = 0 if s1[i-1] == s2[j-1] else 1
                        matrix[i][j] = min(
                            matrix[i-1][j] + 1,      # deletion
                            matrix[i][j-1] + 1,      # insertion
                            matrix[i-1][j-1] + cost  # substitution
                        )
                
                distance = matrix[len(s1)][len(s2)]
                max_len = max(len(s1), len(s2))
                return 1.0 - (distance / max_len) if max_len > 0 else 1.0
            
            levenshtein_sim = levenshtein_similarity(text1, text2)
            
            # Combine similarities with weights
            final_similarity = (
                0.4 * jaccard_sim +      # Word overlap (most important)
                0.3 * ngram_sim +        # Structural similarity
                0.3 * levenshtein_sim    # Character-level similarity
            )
            
            return final_similarity
            
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            # Fallback to simple word overlap
            words1 = set(text1.split())
            words2 = set(text2.split())
            if not words1 or not words2:
                return 0.0
            intersection = len(words1.intersection(words2))
            union = len(words1.union(words2))
            return intersection / union if union > 0 else 0.0
    
    def _generate_revision_suggestion(self, response: str, query: str, documents: List[Document], validation: ResponseValidation) -> str:
        """Generate a revision suggestion to improve response coverage."""
        try:
            # Create a revision prompt based on validation feedback
            available_rids = [doc.metadata.get('rid') for doc in documents if doc.metadata.get('rid')]
            rid_list = ", ".join(available_rids)
            
            revision_prompt = f"""The following response has good accuracy but incomplete coverage. Please extend and improve it to better address the user's question.

Original Query: {query}

Current Response: {response}

Available RIDs for citation: {rid_list}

Instructions:
1. Keep the accurate information from the original response
2. Expand the response to more comprehensively address the query
3. Add missing key points that would improve completeness
4. Ensure proper RID citations are included
5. Target 220-300 words for comprehensive coverage

Enhanced Response:"""
            
            # For now, return a simple enhancement suggestion
            # In production, this would call the LLM with the revision prompt
            logger.info("Revision suggestion generated (placeholder implementation)")
            
            # Return None to indicate no revision available (placeholder)
            return None
            
        except Exception as e:
            logger.error(f"Error generating revision suggestion: {e}")
            return None
    
    def get_validation_statistics(self) -> Dict[str, Any]:
        """Get statistics about validation performance."""
        if not self.validation_history:
            return {}
        
        scores = [v['validation'].overall_score for v in self.validation_history]
        
        return {
            'total_validations': len(self.validation_history),
            'average_score': sum(scores) / len(scores),
            'min_score': min(scores),
            'max_score': max(scores),
            'pass_rate': sum(1 for v in self.validation_history 
                           if v['validation'].overall_result == ValidationResult.PASS) / len(self.validation_history)
        }

# Global validation chain instance
validation_chain = SelfValidationChain(enable_validation=True)