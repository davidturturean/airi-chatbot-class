#!/usr/bin/env python3
"""
Extract query-response pairs from stakeholder test results JSON
Creates a clean, readable file with just the Q&A content
"""
import json
import glob
import os
from datetime import datetime

def find_latest_results_file():
    """Find the most recent stakeholder test results file"""
    pattern = "stakeholder_test_results_*.json"
    files = glob.glob(pattern)
    
    if not files:
        print(f"❌ No files found matching pattern: {pattern}")
        return None
    
    # Sort by modification time to get the latest
    latest_file = max(files, key=os.path.getmtime)
    print(f"📁 Found latest results file: {latest_file}")
    return latest_file

def extract_qa_pairs(json_file):
    """Extract query-response pairs from JSON file"""
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        # Get the detailed results
        results = data.get('detailed_results', [])
        
        if not results:
            print("❌ No results found in JSON file")
            return []
        
        qa_pairs = []
        
        for result in results:
            # Extract query and response
            query = result.get('query', 'No query found')
            response = result.get('response', 'No response found')
            
            # Additional metadata for context
            query_num = result.get('query_num', '?')
            stakeholder = result.get('stakeholder', 'Unknown')
            category = result.get('category', 'Unknown')
            success = result.get('success', False)
            
            qa_pairs.append({
                'number': query_num,
                'query': query,
                'response': response,
                'stakeholder': stakeholder,
                'category': category,
                'success': success
            })
        
        return qa_pairs
    
    except Exception as e:
        print(f"❌ Error reading JSON file: {e}")
        return []

def save_qa_pairs(qa_pairs, output_file):
    """Save Q&A pairs to a formatted text file"""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            # Write header
            f.write("=" * 100 + "\n")
            f.write("EXTRACTED QUERY-RESPONSE PAIRS FROM STAKEHOLDER TEST\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Pairs: {len(qa_pairs)}\n")
            f.write("=" * 100 + "\n\n")
            
            # Statistics
            successful = sum(1 for qa in qa_pairs if qa['success'])
            f.write(f"📊 Statistics:\n")
            f.write(f"  - Total Queries: {len(qa_pairs)}\n")
            f.write(f"  - Successful: {successful}\n")
            f.write(f"  - Failed: {len(qa_pairs) - successful}\n")
            f.write("\n" + "=" * 100 + "\n\n")
            
            # Write each Q&A pair
            for qa in qa_pairs:
                f.write(f"QUERY #{qa['number']} [{qa['stakeholder']} - {qa['category']}]\n")
                f.write("-" * 80 + "\n")
                f.write(f"Q: {qa['query']}\n\n")
                f.write(f"A: {qa['response']}\n")
                f.write("\n" + "=" * 100 + "\n\n")
            
        print(f"✅ Successfully saved {len(qa_pairs)} Q&A pairs to: {output_file}")
        
    except Exception as e:
        print(f"❌ Error saving output file: {e}")

def create_simplified_version(qa_pairs, output_file):
    """Create an even simpler version with just Q and A"""
    simple_file = output_file.replace('.txt', '_simple.txt')
    
    try:
        with open(simple_file, 'w', encoding='utf-8') as f:
            for qa in qa_pairs:
                f.write(f"Q{qa['number']}: {qa['query']}\n\n")
                f.write(f"{qa['response']}\n")
                f.write("\n" + "-" * 50 + "\n\n")
        
        print(f"✅ Also created simplified version: {simple_file}")
        
    except Exception as e:
        print(f"⚠️  Could not create simplified version: {e}")

def main():
    """Main function to extract Q&A pairs"""
    print("🚀 Starting Q&A Extraction from Stakeholder Test Results")
    print("=" * 60)
    
    # Find the latest results file
    json_file = find_latest_results_file()
    
    if not json_file:
        return
    
    # Extract Q&A pairs
    print("📝 Extracting query-response pairs...")
    qa_pairs = extract_qa_pairs(json_file)
    
    if not qa_pairs:
        print("❌ No Q&A pairs found to extract")
        return
    
    print(f"✅ Extracted {len(qa_pairs)} Q&A pairs")
    
    # Save to output file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"qa_pairs_extracted_{timestamp}.txt"
    
    save_qa_pairs(qa_pairs, output_file)
    
    # Create simplified version
    create_simplified_version(qa_pairs, output_file)
    
    print("\n" + "=" * 60)
    print("✅ Extraction complete!")

if __name__ == "__main__":
    main()