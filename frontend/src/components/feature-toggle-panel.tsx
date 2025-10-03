import React, { useState } from 'react';
import { X, Settings, ChevronDown, ChevronUp, RotateCcw } from 'lucide-react';
import { useFeatures } from '@/context/FeatureContext';

interface FeatureTogglePanelProps {
  isOpen: boolean;
  onClose: () => void;
}

export const FeatureTogglePanel: React.FC<FeatureTogglePanelProps> = ({ isOpen, onClose }) => {
  const { features, featureConfig, loading, error, updateFeature, resetToDefaults } = useFeatures();
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set(['core', 'sidebar']));
  const [saving, setSaving] = useState(false);

  if (!isOpen) return null;

  const toggleCategory = (category: string) => {
    setExpandedCategories(prev => {
      const newSet = new Set(prev);
      if (newSet.has(category)) {
        newSet.delete(category);
      } else {
        newSet.add(category);
      }
      return newSet;
    });
  };

  const handleToggle = async (flagName: string, currentValue: boolean) => {
    setSaving(true);
    try {
      await updateFeature(flagName, !currentValue);
    } catch (err) {
      console.error('Failed to update feature:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleReset = async () => {
    if (confirm('Are you sure you want to reset all features to their default values?')) {
      setSaving(true);
      try {
        await resetToDefaults();
      } catch (err) {
        console.error('Failed to reset features:', err);
      } finally {
        setSaving(false);
      }
    }
  };

  // Group features by category
  const featuresByCategory = featureConfig ? Object.entries(featureConfig.flags).reduce((acc, [flagName, metadata]) => {
    const category = metadata.category;
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push({ flagName, ...metadata });
    return acc;
  }, {} as Record<string, Array<{ flagName: string } & typeof featureConfig.flags[string]>>) : {};

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] overflow-hidden">
        {/* Header */}
        <div className="bg-gray-50 px-6 py-4 border-b flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Settings className="w-5 h-5 text-gray-600" />
            <h2 className="text-lg font-semibold">Feature Configuration</h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="overflow-y-auto max-h-[calc(80vh-8rem)]">
          {loading ? (
            <div className="p-6 text-center text-gray-500">Loading features...</div>
          ) : error ? (
            <div className="p-6 text-center text-red-500">Error: {error}</div>
          ) : featureConfig ? (
            <div className="p-6 space-y-4">
              {Object.entries(featuresByCategory).map(([category, categoryFeatures]) => (
                <div key={category} className="border rounded-lg overflow-hidden">
                  <button
                    onClick={() => toggleCategory(category)}
                    className="w-full px-4 py-3 bg-gray-50 hover:bg-gray-100 transition flex items-center justify-between"
                  >
                    <span className="font-medium text-gray-700">
                      {featureConfig.categories[category] || category}
                    </span>
                    {expandedCategories.has(category) ? (
                      <ChevronUp className="w-4 h-4 text-gray-400" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-gray-400" />
                    )}
                  </button>
                  
                  {expandedCategories.has(category) && (
                    <div className="p-4 space-y-3">
                      {categoryFeatures.map(feature => (
                        <div key={feature.flagName} className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <label className="font-medium text-gray-700">
                                {feature.label}
                              </label>
                              {feature.requiresRestart && (
                                <span className="text-xs bg-yellow-100 text-yellow-700 px-2 py-1 rounded">
                                  Requires restart
                                </span>
                              )}
                            </div>
                            <p className="text-sm text-gray-500 mt-1">{feature.description}</p>
                          </div>
                          <button
                            onClick={() => handleToggle(feature.flagName, features[feature.flagName])}
                            disabled={saving}
                            className={`
                              relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full
                              transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2
                              ${features[feature.flagName] ? 'bg-red-500' : 'bg-gray-300'}
                              ${saving ? 'opacity-50 cursor-not-allowed' : ''}
                            `}
                          >
                            <span
                              className={`
                                pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow
                                transition duration-200 ease-in-out
                                ${features[feature.flagName] ? 'translate-x-5' : 'translate-x-0'}
                              `}
                            />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="p-6 text-center text-gray-500">No feature configuration available</div>
          )}
        </div>

        {/* Footer */}
        <div className="bg-gray-50 px-6 py-3 border-t flex items-center justify-between">
          <button
            onClick={handleReset}
            disabled={saving}
            className="flex items-center gap-2 px-4 py-2 text-gray-600 hover:text-gray-800 transition disabled:opacity-50"
          >
            <RotateCcw className="w-4 h-4" />
            Reset to Defaults
          </button>
          <div className="text-sm text-gray-500">
            Press <kbd className="px-2 py-1 bg-gray-200 rounded text-xs">
              {navigator.platform.toUpperCase().indexOf('MAC') >= 0 ? 'Cmd' : 'Ctrl'}+Shift+F
            </kbd> to toggle this panel
          </div>
        </div>
      </div>
    </div>
  );
};