"""
Language-aware message utilities for consistent multilingual support.
"""
from typing import Optional
from ..config.logging import get_logger

logger = get_logger(__name__)

def get_language_aware_message(english_message: str, user_query: str, gemini_model=None) -> str:
    """
    Returns a message in the appropriate language based on the user's query.
    
    Defaults to English unless the query is CLEARLY in another language.
    This follows the same principle as our main language consistency approach.
    
    Args:
        english_message: The message in English to potentially translate
        user_query: The original user query to detect language from
        gemini_model: Optional Gemini model instance for translation
        
    Returns:
        The message in the appropriate language
    """
    # If no model available, return English
    if not gemini_model:
        logger.debug("No Gemini model available for translation, returning English message")
        return english_message
    
    # Create prompt following our successful language detection pattern
    prompt = f"""User Query (detect the language): {user_query}

English message to potentially translate: {english_message}

CRITICAL INSTRUCTIONS:
1. Detect the language of the user's query above
2. If the query is in English, return the English message as-is (THIS IS THE DEFAULT - MOST QUERIES ARE IN ENGLISH)
3. Only translate if the query is CLEARLY in another language (French, Spanish, German, etc.)
4. When in doubt, use English
5. Maintain the same meaning and tone when translating
6. Return ONLY the message text, no explanations or metadata

Your response must be ONLY the message (either the original English or the translation)."""
    
    try:
        # Use Gemini to detect language and translate if needed
        translated = gemini_model.generate(prompt, [])
        logger.debug(f"Successfully generated language-aware message for query: {user_query[:50]}...")
        return translated.strip()
    except Exception as e:
        logger.warning(f"Failed to generate language-aware message: {e}")
        # Fallback to English on any error
        return english_message

def get_no_results_message(user_query: str, gemini_model=None) -> str:
    """
    Returns a "no results found" message in the appropriate language.
    
    Args:
        user_query: The original user query to detect language from
        gemini_model: Optional Gemini model instance for translation
        
    Returns:
        "No results found" message in the appropriate language
    """
    english_message = "No results found for your query."
    return get_language_aware_message(english_message, user_query, gemini_model)

def get_out_of_scope_message(user_query: str, gemini_model=None) -> str:
    """
    Returns an "out of scope" message in the appropriate language.
    
    Args:
        user_query: The original user query to detect language from
        gemini_model: Optional Gemini model instance for translation
        
    Returns:
        "Out of scope" message in the appropriate language
    """
    english_message = "This query is outside the scope of the AI Risk Repository. Please ask about AI-related risks, safety, bias, privacy, or governance topics."
    return get_language_aware_message(english_message, user_query, gemini_model)