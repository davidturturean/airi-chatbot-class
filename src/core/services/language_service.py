"""
Language detection and management service.
"""
import json
import os
from typing import Dict, List, Optional, Any
from pathlib import Path
from difflib import get_close_matches

from ...config.logging import get_logger

logger = get_logger(__name__)

class LanguageService:
    """Service for language detection, validation, and management."""
    
    def __init__(self, gemini_model=None):
        """
        Initialize the language service.
        
        Args:
            gemini_model: Optional Gemini model for language detection
        """
        self.gemini_model = gemini_model
        self.languages = self._load_language_database()
        self.language_by_code = {lang['code']: lang for lang in self.languages}
        
        # Build search indices for autocomplete
        self.native_names = {lang['native_name'].lower(): lang['code'] for lang in self.languages}
        self.english_names = {lang['english_name'].lower(): lang['code'] for lang in self.languages}
        
    def _load_language_database(self) -> List[Dict[str, Any]]:
        """Load language database from JSON file."""
        try:
            json_path = Path(__file__).parent.parent.parent / 'data' / 'languages.json'
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data['languages']
        except Exception as e:
            logger.error(f"Failed to load language database: {e}")
            # Return minimal fallback languages
            return [
                {"code": "en", "native_name": "English", "english_name": "English", "category": "major"},
                {"code": "es", "native_name": "Español", "english_name": "Spanish", "category": "major"},
                {"code": "fr", "native_name": "Français", "english_name": "French", "category": "major"},
            ]
    
    def detect_language(self, text: str) -> Dict[str, Any]:
        """
        Detect language from text using Gemini.
        
        Args:
            text: Text to analyze
            
        Returns:
            Language info dict with code, names, confidence, category
        """
        if not self.gemini_model:
            logger.warning("No Gemini model available, defaulting to English")
            return self.get_language_info("en")
        
        # Build language list for prompt
        language_list = "\n".join([
            f"{lang['code']}: {lang['english_name']} ({lang['native_name']})"
            for lang in self.languages[:100]  # Limit to avoid token issues
        ])
        
        prompt = f"""Detect the language of this text: "{text}"

IMPORTANT: DEFAULT TO ENGLISH unless the text is CLEARLY in another language.
When in doubt, choose English (code: "en").

Choose from these supported languages (showing first 100):
{language_list}

If it's a regional dialect, be specific (e.g., "lim" for Limburgish, not "nl" for Dutch).
If it's clearly a fun/constructed language pattern (like Yoda speak), identify it.

Return ONLY a JSON object with this exact format:
{{
    "code": "language code from the list",
    "confidence": 0.95
}}

IMPORTANT: Return ONLY the JSON, no explanation."""

        try:
            response = self.gemini_model.generate(prompt, [])
            
            # Clean and parse response
            response_text = response.strip()
            # Remove any markdown code blocks
            if "```" in response_text:
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            import json
            result = json.loads(response_text)
            
            # Get full language info
            language_info = self.get_language_info(result.get('code', 'en'))
            if language_info:
                language_info['confidence'] = result.get('confidence', 0.9)
                return language_info
                
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
        
        # Default to English
        return self.get_language_info("en")
    
    def get_language_info(self, code: str) -> Optional[Dict[str, Any]]:
        """Get full language information by code."""
        return self.language_by_code.get(code)
    
    def validate_language_input(self, user_input: str) -> Optional[Dict[str, Any]]:
        """
        Validate and autocomplete user language input.
        
        Args:
            user_input: Partial language name or code
            
        Returns:
            Best matching language info or None
        """
        user_input = user_input.lower().strip()
        
        # Direct code match
        if user_input in self.language_by_code:
            return self.language_by_code[user_input]
        
        # Search in native names
        matches = get_close_matches(user_input, self.native_names.keys(), n=1, cutoff=0.6)
        if matches:
            code = self.native_names[matches[0]]
            return self.language_by_code[code]
        
        # Search in English names
        matches = get_close_matches(user_input, self.english_names.keys(), n=1, cutoff=0.6)
        if matches:
            code = self.english_names[matches[0]]
            return self.language_by_code[code]
        
        # Partial match in any field
        for lang in self.languages:
            if user_input in lang['code'].lower() or \
               user_input in lang['native_name'].lower() or \
               user_input in lang['english_name'].lower():
                return lang
        
        return None
    
    def autocomplete_languages(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get autocomplete suggestions for language search.
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            List of matching languages
        """
        query = query.lower().strip()
        if not query:
            return self.languages[:limit]
        
        results = []
        
        # Exact matches first
        for lang in self.languages:
            if query == lang['code'].lower() or \
               query == lang['native_name'].lower() or \
               query == lang['english_name'].lower():
                results.append(lang)
                if len(results) >= limit:
                    return results
        
        # Prefix matches
        for lang in self.languages:
            if lang not in results and (
                lang['code'].lower().startswith(query) or
                lang['native_name'].lower().startswith(query) or
                lang['english_name'].lower().startswith(query)
            ):
                results.append(lang)
                if len(results) >= limit:
                    return results
        
        # Contains matches
        for lang in self.languages:
            if lang not in results and (
                query in lang['code'].lower() or
                query in lang['native_name'].lower() or
                query in lang['english_name'].lower()
            ):
                results.append(lang)
                if len(results) >= limit:
                    return results
        
        return results
    
    def get_language_prompt(self, language_code: str) -> str:
        """
        Get language-specific prompt instructions.
        
        Args:
            language_code: Language code
            
        Returns:
            Prompt instructions for the language
        """
        special_prompts = {
            'yoda': "Respond using Yoda's speech pattern (object-subject-verb word order). Example: 'Strong in the Force, you are.'",
            'pirate': "Respond in pirate speak (arr, matey, treasure, ahoy, etc.). Be colorful and nautical!",
            'shakespeare': "Respond in Shakespearean English (thou, thee, thy, dost, hath). Be eloquent and poetic.",
            'uwu': "Wespond using UwU speak (repwace r with w, add cute emoticons UwU, OwO, >w<).",
            'l33t': "R3sp0nd u51ng 1337 5p34k (r3pl4c3 l3tt3r5 w1th numb3r5).",
            'doge': "Respond in doge speak. Much language. Very response. So helpful. Wow.",
            'klingon': "Try to respond fully in Klingon. If impossible, mix with English. Use: 'nuqneH' (what do you want), 'Qapla'' (success), 'petaQ' (fool), 'HIja'' (yes), 'ghobe'' (no), 'jup' (friend), 'jagh' (enemy), 'yap' (enough), 'Qob' (danger), 'naDev' (here), 'voD' (now), 'veb' (next), 'DIlo'' (we use), 'DIcha'' (we identify), ''e' vIl' (I see).",
            'elvish-sindarin': "Try to respond fully in Sindarin Elvish. If impossible, mix with English. Use: 'Mae govannen' (well met), 'Le hannon' (thank you), 'Goheno nin' (forgive me), 'Mellon' (friend), 'Annon' (gate), 'Naur' (fire), 'Orch' (enemy), 'Estel' (hope), 'Im' (I am), 'Le' (you), 'Nin' (my), 'Adar' (father), 'Naneth' (mother).",
            'elvish-quenya': "Try to respond fully in Quenya Elvish. If impossible, mix with English. Use: 'Aiya' (hail), 'Namárië' (farewell), 'Hantanyel' (thank you), 'Meldo' (friend), 'Aurë' (day), 'Laurë' (gold), 'Nár' (fire), 'Vilya' (air), 'Arda' (earth), 'Ni' (I), 'Lye' (you), 'Nya' (my).",
            'dothraki': "Try to respond fully in Dothraki. If impossible, mix with English. Use: 'M'athchomaroon' (hello), 'Hajas' (goodbye), 'San athchomari yeraan' (thank you), 'Sek' (yes), 'Vos' (no), 'Arakh' (sword), 'Dothrak' (ride), 'Khaleesi' (queen), 'Khal' (leader), 'Shekh ma shieraki anni' (my sun and stars).",
            'valyrian': "Try to respond fully in High Valyrian. If impossible, mix with English. Use: 'Valar morghulis' (all men must die), 'Valar dohaeris' (all men must serve), 'Dracarys' (dragonfire), 'Kirimvose' (thank you), 'Sōvēs' (fly), 'Rytsas' (hello), 'Geros ilas' (goodbye), 'Kessa' (yes), 'Daor' (no), 'Ñuha' (my), 'Aōha' (your), 'Ziry' (it/he/she), 'Īlva' (we).",
            'navi': "Try to respond fully in Na'vi. If impossible, mix with English. Use: 'Kaltxì' (hello), 'Oel ngati kameie' (I see you), 'Irayo' (thank you), 'Kìyevame' (goodbye), 'Srane' (yes), 'Kehe' (no), 'Eywa' (deity), 'Toruk' (last shadow), 'Ikran' (banshee), 'Olo'eyktan' (clan leader)."
        }
        
        if language_code in special_prompts:
            return special_prompts[language_code]
        
        # Get language info
        lang_info = self.get_language_info(language_code)
        if lang_info:
            if lang_info['category'] == 'regional':
                return f"Respond in {lang_info['english_name']} ({lang_info['native_name']}) dialect if possible."
            else:
                return f"Respond in {lang_info['english_name']} ({lang_info['native_name']})."
        
        return "Respond in the same language as the user's query."
    
    def get_all_languages(self) -> List[Dict[str, Any]]:
        """Get all supported languages."""
        return self.languages
    
    def get_languages_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get languages filtered by category."""
        return [lang for lang in self.languages if lang.get('category') == category]

# Global language service instance
language_service = LanguageService()