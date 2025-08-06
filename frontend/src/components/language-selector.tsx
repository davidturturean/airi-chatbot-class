import React, { useState, useEffect, useRef } from 'react';
import { ChevronDown, Globe, Check } from 'lucide-react';

interface LanguageInfo {
  code: string;
  native_name: string;
  english_name: string;
  category: string;
  display_name?: string;
}

interface LanguageSelectorProps {
  sessionId: string;
  currentLanguage?: LanguageInfo | null;
  onLanguageChange: (language: LanguageInfo) => void;
}

export const LanguageSelector: React.FC<LanguageSelectorProps> = ({
  sessionId,
  currentLanguage,
  onLanguageChange
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [suggestions, setSuggestions] = useState<LanguageInfo[]>([]);
  const [allLanguages, setAllLanguages] = useState<LanguageInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Fetch all languages on mount
  useEffect(() => {
    fetchLanguages();
  }, []);

  // Handle click outside to close dropdown
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const fetchLanguages = async () => {
    try {
      const response = await fetch('/api/supported-languages');
      const data = await response.json();
      // Filter out fun languages and sort alphabetically by native name
      const languages = (data.languages || [])
        .filter((lang: LanguageInfo) => lang.category !== 'fun')
        .sort((a: LanguageInfo, b: LanguageInfo) => 
          a.native_name.localeCompare(b.native_name)
        );
      setAllLanguages(languages);
      // Show all languages alphabetically
      setSuggestions(languages);
    } catch (error) {
      console.error('Failed to fetch languages:', error);
    }
  };

  const searchLanguages = async (query: string) => {
    if (!query.trim()) {
      // Show all languages when empty
      setSuggestions(allLanguages);
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('/api/autocomplete-language', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, limit: 15 })
      });
      const data = await response.json();
      // Filter out fun category from suggestions
      const filtered = (data.suggestions || []).filter(
        (lang: LanguageInfo) => lang.category !== 'fun'
      );
      setSuggestions(filtered);
    } catch (error) {
      console.error('Failed to search languages:', error);
      // Fallback to client-side filtering
      const filtered = allLanguages.filter(lang =>
        lang.native_name.toLowerCase().includes(query.toLowerCase()) ||
        lang.english_name.toLowerCase().includes(query.toLowerCase()) ||
        lang.code.toLowerCase().includes(query.toLowerCase())
      );
      setSuggestions(filtered.slice(0, 15));
    } finally {
      setLoading(false);
    }
  };

  const handleLanguageSelect = async (language: LanguageInfo) => {
    try {
      const response = await fetch('/api/set-session-language', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          language_code: language.code
        })
      });

      if (response.ok) {
        onLanguageChange(language);
        setIsOpen(false);
        setSearchQuery('');
      }
    } catch (error) {
      console.error('Failed to set language:', error);
    }
  };

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const query = e.target.value;
    setSearchQuery(query);
    searchLanguages(query);
  };

  const handleKeyPress = async (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && searchQuery.trim()) {
      // Try to validate the typed language (allows Easter eggs)
      try {
        const response = await fetch('/api/validate-language', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ input: searchQuery.trim() })
        });
        const data = await response.json();
        
        if (data.valid && data.language) {
          handleLanguageSelect(data.language);
        }
      } catch (error) {
        console.error('Failed to validate language:', error);
      }
    }
  };

  const getDisplayName = (lang: LanguageInfo) => {
    if (lang.code === 'en') return 'English';
    return `${lang.native_name} (${lang.english_name})`;
  };

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Main Button */}
      <button
        onClick={() => {
          if (!isOpen) {
            // Opening the dropdown - reset search state
            setSearchQuery('');
            // Show all languages alphabetically
            setSuggestions(allLanguages);
          }
          setIsOpen(!isOpen);
        }}
        className="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900 
                   border border-gray-200 rounded-lg hover:border-gray-300 transition-all
                   bg-white hover:bg-gray-50"
      >
        <Globe className="w-4 h-4" />
        <span className="font-medium">
          {currentLanguage ? getDisplayName(currentLanguage) : 'English'}
        </span>
        <ChevronDown className={`w-3 h-3 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-lg border border-gray-200 z-50">
          {/* Search Input */}
          <div className="p-3 border-b border-gray-100">
            <input
              ref={inputRef}
              type="text"
              value={searchQuery}
              onChange={handleSearchChange}
              onKeyPress={handleKeyPress}
              placeholder="Search or type a language..."
              className="w-full px-3 py-2 text-sm border border-gray-200 rounded-md 
                       focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              autoFocus
            />
          </div>

          {/* Language List */}
          <div className="max-h-80 overflow-y-auto">
            {loading ? (
              <div className="p-4 text-center text-sm text-gray-500">
                Searching...
              </div>
            ) : suggestions.length > 0 ? (
              <div className="py-1">
                {suggestions.map((lang) => (
                  <button
                    key={lang.code}
                    onClick={() => handleLanguageSelect(lang)}
                    className="w-full px-3 py-2 text-left hover:bg-gray-50 flex items-center justify-between
                             group transition-colors"
                  >
                    <div>
                      <div className="text-sm font-medium text-gray-900">
                        {lang.native_name}
                      </div>
                      {lang.code !== 'en' && (
                        <div className="text-xs text-gray-500">
                          {lang.english_name}
                        </div>
                      )}
                    </div>
                    {currentLanguage?.code === lang.code && (
                      <Check className="w-4 h-4 text-blue-600" />
                    )}
                  </button>
                ))}
              </div>
            ) : searchQuery ? (
              <div className="p-4 text-center text-sm text-gray-500">
                No languages found
                <div className="text-xs mt-1 text-gray-400">
                  Press Enter to try your input
                </div>
              </div>
            ) : (
              <div className="p-4 text-center text-sm text-gray-500">
                Scroll for more languages or type to search
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};