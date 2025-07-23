#!/usr/bin/env python3
"""
Real-time viewer for stakeholder test progress
Run this in a separate terminal to watch test progress live
"""
import json
import time
import os
from datetime import datetime

def clear_screen():
    """Clear terminal screen"""
    os.system('clear' if os.name == 'posix' else 'cls')

def format_time_remaining(current, total, avg_time_per_query):
    """Estimate time remaining"""
    remaining = total - current
    seconds_left = remaining * avg_time_per_query
    
    hours = int(seconds_left // 3600)
    minutes = int((seconds_left % 3600) // 60)
    seconds = int(seconds_left % 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

def watch_progress():
    """Watch test progress in real-time"""
    progress_file = "stakeholder_test_progress.json"
    
    print("🔍 Watching stakeholder test progress...")
    print(f"📁 Monitoring file: {progress_file}")
    print("Press Ctrl+C to stop watching\n")
    
    last_query_num = 0
    start_time = time.time()
    
    while True:
        try:
            if os.path.exists(progress_file):
                with open(progress_file, 'r') as f:
                    data = json.load(f)
                
                current_query = data['current_query']
                total_queries = data['total_queries']
                results = data['results_so_far']
                
                # Only update if there's new data
                if current_query != last_query_num:
                    clear_screen()
                    
                    # Calculate statistics
                    elapsed_time = time.time() - start_time
                    avg_time_per_query = elapsed_time / current_query if current_query > 0 else 0
                    
                    successful = sum(1 for r in results if r.get('success', False))
                    failed = len(results) - successful
                    
                    # Print header
                    print("🚀 STAKEHOLDER TEST PROGRESS")
                    print("=" * 80)
                    print(f"📊 Progress: {current_query}/{total_queries} ({current_query/total_queries*100:.1f}%)")
                    print(f"⏱️  Elapsed: {int(elapsed_time)}s | Est. Remaining: {format_time_remaining(current_query, total_queries, avg_time_per_query)}")
                    print(f"✅ Successful: {successful} | ❌ Failed: {failed}")
                    print("=" * 80)
                    
                    # Show last 5 queries
                    print("\n📝 Recent Queries:")
                    print("-" * 80)
                    
                    recent_results = results[-5:] if len(results) > 5 else results
                    for r in recent_results:
                        if r.get('success', False):
                            quality_score = r.get('quality_analysis', {}).get('quality_score', 0)
                            response_time = r.get('response_time', 0)
                            print(f"✅ [{r['query_num']}] {r['stakeholder']} - {r['category']}")
                            print(f"   Query: {r['query'][:60]}...")
                            print(f"   Score: {quality_score:.1f}/100 | Time: {response_time:.2f}s")
                            
                            # Show response preview
                            if 'response' in r:
                                preview = r['response'][:150].replace('\n', ' ')
                                print(f"   Response: {preview}...")
                        else:
                            print(f"❌ [{r['query_num']}] Failed: {r.get('error', 'Unknown error')}")
                        print()
                    
                    # Show quality statistics
                    if successful > 0:
                        avg_quality = sum(r.get('quality_analysis', {}).get('quality_score', 0) 
                                        for r in results if r.get('success', False)) / successful
                        print("-" * 80)
                        print(f"📈 Average Quality Score: {avg_quality:.1f}/100")
                        
                        # Stakeholder breakdown
                        stakeholder_scores = {}
                        for r in results:
                            if r.get('success', False):
                                stakeholder = r['stakeholder']
                                score = r.get('quality_analysis', {}).get('quality_score', 0)
                                if stakeholder not in stakeholder_scores:
                                    stakeholder_scores[stakeholder] = []
                                stakeholder_scores[stakeholder].append(score)
                        
                        print("\n👥 Stakeholder Performance:")
                        for stakeholder, scores in stakeholder_scores.items():
                            avg_score = sum(scores) / len(scores)
                            print(f"  {stakeholder}: {avg_score:.1f}/100 ({len(scores)} queries)")
                    
                    last_query_num = current_query
                    
                    # Show timestamp
                    print(f"\n🕐 Last updated: {datetime.now().strftime('%H:%M:%S')}")
                    
            else:
                print("⏳ Waiting for test to start...")
            
            time.sleep(2)  # Check every 2 seconds
            
        except KeyboardInterrupt:
            print("\n\n👋 Stopped watching test progress")
            break
        except Exception as e:
            print(f"Error reading progress: {e}")
            time.sleep(5)

if __name__ == "__main__":
    watch_progress()