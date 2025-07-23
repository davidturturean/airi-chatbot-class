#!/usr/bin/env python3
"""
Real-time FULL RESPONSE viewer for stakeholder test
Shows complete responses as they are generated
"""
import json
import time
import os
from datetime import datetime

def watch_full_responses():
    """Watch test with full responses in real-time"""
    progress_file = "stakeholder_test_progress.json"
    
    print("🔍 FULL RESPONSE VIEWER - Stakeholder Test")
    print(f"📁 Monitoring: {progress_file}")
    print("=" * 100)
    print("Press Ctrl+C to stop\n")
    
    seen_queries = set()
    
    while True:
        try:
            if os.path.exists(progress_file):
                with open(progress_file, 'r') as f:
                    data = json.load(f)
                
                results = data['results_so_far']
                
                # Show new results only
                for r in results:
                    query_id = r.get('query_num', 0)
                    if query_id not in seen_queries and r.get('success', False):
                        seen_queries.add(query_id)
                        
                        # Print full details
                        print("\n" + "="*100)
                        print(f"🆕 QUERY #{query_id}/{data['total_queries']}")
                        print("="*100)
                        print(f"👤 Stakeholder: {r['stakeholder']}")
                        print(f"📁 Category: {r['category']}")
                        print(f"🔧 Complexity: {r['complexity']}")
                        print(f"⏱️  Response Time: {r.get('response_time', 0):.2f}s")
                        print(f"📈 Quality Score: {r.get('quality_analysis', {}).get('quality_score', 0):.1f}/100")
                        print(f"📄 Documents Found: {r.get('documents_found', 0)}")
                        
                        # Quality details
                        qa = r.get('quality_analysis', {})
                        print(f"\n📊 Quality Analysis:")
                        print(f"  - Expected Elements: {qa.get('has_expected_elements', 0)}/{len(r.get('expected_elements', []))}")
                        print(f"  - Has Citations: {'Yes' if qa.get('has_citations', False) else 'No'}")
                        print(f"  - Well Structured: {'Yes' if qa.get('has_structure', False) else 'No'}")
                        print(f"  - Stakeholder Appropriate: {'Yes' if qa.get('stakeholder_appropriate', False) else 'No'}")
                        print(f"  - Complexity Appropriate: {'Yes' if qa.get('complexity_appropriate', False) else 'No'}")
                        
                        if qa.get('missing_elements'):
                            print(f"  - Missing Elements: {', '.join(qa['missing_elements'])}")
                        
                        print(f"\n❓ QUERY:")
                        print("-" * 100)
                        print(r['query'])
                        
                        print(f"\n💬 FULL RESPONSE:")
                        print("-" * 100)
                        print(r.get('response', 'No response captured'))
                        print("-" * 100)
                        
                        print(f"\n🕐 Generated at: {datetime.now().strftime('%H:%M:%S')}")
                        print("\n" + "⬇️ "*20 + "\n")
            
            time.sleep(1)  # Check every second
            
        except KeyboardInterrupt:
            print("\n\n👋 Stopped watching")
            break
        except Exception as e:
            # Silently continue on errors (file might be mid-write)
            time.sleep(1)

if __name__ == "__main__":
    watch_full_responses()