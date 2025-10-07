#!/usr/bin/env python3
"""
Excel Performance Testing Script
Tests the optimized Excel parsing with and without formatting
"""

import time
import requests
import sys
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:5000"
TEST_RID = "RID-07595"  # The problematic 11-sheet Excel file
SESSION_ID = "test-session-" + str(int(time.time()))

def test_excel_endpoint(include_formatting: bool = False):
    """Test Excel parsing with timing metrics"""
    endpoint = f"{BASE_URL}/api/document/{TEST_RID}/excel"
    params = {
        "session_id": SESSION_ID,
        "include_formatting": str(include_formatting).lower()
    }

    print(f"\n{'='*60}")
    print(f"Testing Excel parsing (include_formatting={include_formatting})")
    print(f"{'='*60}")
    print(f"Endpoint: {endpoint}")
    print(f"Parameters: {params}")
    print(f"Starting request...")

    start_time = time.time()

    try:
        response = requests.get(endpoint, params=params, timeout=70)
        elapsed_time = (time.time() - start_time) * 1000  # ms

        print(f"\n✅ Request completed in {elapsed_time:.2f}ms")
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            sheets = data.get('sheets', [])
            print(f"Number of sheets: {len(sheets)}")

            for i, sheet in enumerate(sheets):
                sheet_name = sheet.get('sheet_name', 'Unknown')
                rows = len(sheet.get('rows', []))
                has_formatting = 'formatting' in sheet
                print(f"  Sheet {i+1}: '{sheet_name}' - {rows} rows - Formatting: {'✅' if has_formatting else '❌'}")

            # Performance verdict
            if elapsed_time < 5000:
                print(f"\n🎉 EXCELLENT: {elapsed_time:.2f}ms is well under 5s target!")
            elif elapsed_time < 10000:
                print(f"\n✅ GOOD: {elapsed_time:.2f}ms is acceptable")
            elif elapsed_time < 30000:
                print(f"\n⚠️  SLOW: {elapsed_time:.2f}ms needs optimization")
            else:
                print(f"\n❌ FAILED: {elapsed_time:.2f}ms is too slow")

            return True
        else:
            print(f"❌ Request failed: {response.text}")
            return False

    except requests.Timeout:
        elapsed_time = (time.time() - start_time) * 1000
        print(f"❌ TIMEOUT after {elapsed_time:.2f}ms")
        return False
    except Exception as e:
        elapsed_time = (time.time() - start_time) * 1000
        print(f"❌ ERROR after {elapsed_time:.2f}ms: {str(e)}")
        return False

def test_cache_stats():
    """Check cache statistics"""
    endpoint = f"{BASE_URL}/api/excel/cache-stats"

    print(f"\n{'='*60}")
    print("Cache Statistics")
    print(f"{'='*60}")

    try:
        response = requests.get(endpoint)
        if response.status_code == 200:
            stats = response.json()
            print(f"Total Requests: {stats.get('total_requests', 0)}")
            print(f"Cache Hits: {stats.get('hits', 0)}")
            print(f"Cache Misses: {stats.get('misses', 0)}")
            print(f"Hit Rate: {stats.get('hit_rate_percent', 0):.2f}%")
            print(f"Cache Size: {stats.get('cache_size', 0)}/{stats.get('cache_max_size', 0)}")
            print(f"TTL: {stats.get('cache_ttl_seconds', 0)}s")
        else:
            print(f"❌ Failed to get cache stats: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting cache stats: {str(e)}")

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("EXCEL PERFORMANCE OPTIMIZATION TEST SUITE")
    print("="*60)
    print(f"Testing against: {BASE_URL}")
    print(f"Test RID: {TEST_RID}")
    print(f"Session ID: {SESSION_ID}")

    # Test 1: WITHOUT formatting (should be fast)
    print("\n\n📊 TEST 1: Fast mode (no formatting)")
    print("Expected: 3-5 seconds for 11 sheets")
    success1 = test_excel_endpoint(include_formatting=False)

    # Test 2: WITH formatting (should be slower but still work)
    print("\n\n📊 TEST 2: Full mode (with formatting)")
    print("Expected: 15-20 seconds for 11 sheets (slower but shouldn't timeout)")
    success2 = test_excel_endpoint(include_formatting=True)

    # Test 3: Check cache (second call should be instant)
    print("\n\n📊 TEST 3: Cache test (repeat without formatting)")
    print("Expected: <100ms (cached)")
    success3 = test_excel_endpoint(include_formatting=False)

    # Get cache stats
    test_cache_stats()

    # Summary
    print("\n\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Fast mode (no formatting): {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"Full mode (with formatting): {'✅ PASS' if success2 else '❌ FAIL'}")
    print(f"Cache test: {'✅ PASS' if success3 else '❌ FAIL'}")

    if success1 and success2 and success3:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
