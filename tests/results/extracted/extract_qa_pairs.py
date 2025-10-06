#!/usr/bin/env python3
"""
Extract queries and responses from the test results JSON file
"""
import json

# Load the test results
with open('test_results_105_prompts_updated_20250724_143815.json', 'r') as f:
    data = json.load(f)

# Extract Q&A pairs
qa_pairs = []
for result in data['detailed_results']:
    if result.get('success'):
        qa_pair = {
            'query_num': result['query_num'],
            'query': result['query'],
            'response': result.get('response_full', '')
        }
        qa_pairs.append(qa_pair)

# Save to a new file
output = {
    'total_queries': len(qa_pairs),
    'qa_pairs': qa_pairs
}

with open('extracted_qa_pairs.json', 'w') as f:
    json.dump(output, f, indent=2)

# Also create a markdown version for easy reading
with open('extracted_qa_pairs.md', 'w') as f:
    f.write("# Extracted Q&A Pairs from 105 Prompts Test\n\n")
    
    for qa in qa_pairs:
        f.write(f"## Query #{qa['query_num']}\n\n")
        f.write(f"**Question:** {qa['query']}\n\n")
        f.write(f"**Answer:**\n{qa['response']}\n\n")
        f.write("---\n\n")

print(f"Extracted {len(qa_pairs)} Q&A pairs")
print("Saved to: extracted_qa_pairs.json and extracted_qa_pairs.md")