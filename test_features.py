#!/usr/bin/env python3
"""Test feature flags system."""

from src.config.feature_flags import feature_flags

print("Testing Feature Flags System")
print("=" * 50)

# Test getting all features
print("\nCurrent feature flags:")
all_flags = feature_flags.get_all()
for flag, value in all_flags.items():
    print(f"  {flag}: {value}")

# Test setting a feature
print("\n\nTesting feature update:")
print("Setting SHOW_RELATED_DOCUMENTS to True...")
success = feature_flags.set("SHOW_RELATED_DOCUMENTS", True)
print(f"Update success: {success}")
print(f"New value: {feature_flags.get('SHOW_RELATED_DOCUMENTS')}")

# Test sidebar check
print(f"\nIs sidebar enabled? {feature_flags.is_sidebar_enabled()}")

# Test multiple updates
print("\n\nTesting multiple updates:")
updates = {
    "SHOW_PERSONALIZED_QUESTIONS": True,
    "SHOW_GENERAL_TOPICS": True,
    "SHOW_DEBUG_INFO": True
}
results = feature_flags.update_multiple(updates)
print(f"Update results: {results}")
print(f"Is sidebar enabled now? {feature_flags.is_sidebar_enabled()}")

# Test frontend config
print("\n\nFrontend configuration:")
config = feature_flags.get_frontend_config()
print(f"Categories: {list(config['categories'].values())}")
print(f"Number of features: {len(config['flags'])}")

# Show a sample feature config
sample_flag = "SHOW_LANGUAGE_SELECTOR"
if sample_flag in config['flags']:
    print(f"\nSample feature config for {sample_flag}:")
    for key, value in config['flags'][sample_flag].items():
        print(f"  {key}: {value}")

print("\n" + "=" * 50)
print("Feature flags test completed successfully!")