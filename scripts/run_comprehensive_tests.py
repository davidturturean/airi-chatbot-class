#!/usr/bin/env python3
"""
Comprehensive test runner for the AIRI chatbot.
Runs all test queries (200+) and generates detailed reports.
"""
import sys
import json
import time
import argparse
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import csv
import html
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.services.metrics_service import metrics_service


class ComprehensiveTestRunner:
    """Run comprehensive tests against the chatbot API."""
    
    def __init__(self, api_url: str = "http://localhost:5000", batch_size: int = 5):
        self.api_url = api_url
        self.batch_size = batch_size
        self.test_results = []
        self.start_time = None
        self.end_time = None
    
    def load_test_queries(self) -> Dict[str, List[Dict]]:
        """Load all test queries from golden test set."""
        test_sets = {}
        test_dir = project_root / "tests" / "e2e" / "golden_test_set"
        
        # Load new test categories
        for category in ["edge_cases", "multilingual", "complex_analytical", "out_of_scope"]:
            file_path = test_dir / f"{category}.json"
            if file_path.exists():
                with open(file_path) as f:
                    test_sets[category] = json.load(f)["queries"]
            else:
                print(f"Warning: {file_path} not found")
        
        # Load existing 105 queries if available
        legacy_file = project_root / "tests" / "e2e" / "105_prompts" / "stakeholder_test_results_20250722_202329.json"
        if legacy_file.exists():
            with open(legacy_file) as f:
                legacy_data = json.load(f)
                if "test_cases" in legacy_data:
                    test_sets["legacy_105"] = [
                        {
                            "id": f"legacy_{i:03d}",
                            "query": tc.get("input", ""),
                            "expected_behavior": "general_query"
                        }
                        for i, tc in enumerate(legacy_data["test_cases"][:105])
                    ]
        
        return test_sets
    
    def run_single_query(self, query_data: Dict[str, Any], category: str) -> Dict[str, Any]:
        """Run a single test query and capture metrics."""
        query_id = query_data.get("id", "unknown")
        query_text = query_data.get("query", "")
        
        if not query_text:
            return {
                "id": query_id,
                "category": category,
                "query": query_text,
                "status": "skipped",
                "reason": "empty_query"
            }
        
        start = time.time()
        
        try:
            # Make API request
            response = requests.post(
                f"{self.api_url}/api/v1/sendMessage",
                json={
                    "message": query_text,
                    "session_id": f"test_{category}_{query_id}",
                    "language_code": query_data.get("language")
                },
                timeout=30
            )
            
            latency_ms = int((time.time() - start) * 1000)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "id": query_id,
                    "category": category,
                    "query": query_text[:100],
                    "response": result.get("response", "")[:200],
                    "status": "success",
                    "latency_ms": latency_ms,
                    "language": query_data.get("language", "en"),
                    "expected_behavior": query_data.get("expected_behavior"),
                    "metrics": result.get("metrics", {})
                }
            else:
                return {
                    "id": query_id,
                    "category": category,
                    "query": query_text[:100],
                    "status": "error",
                    "error": f"HTTP {response.status_code}",
                    "latency_ms": latency_ms
                }
        
        except requests.Timeout:
            return {
                "id": query_id,
                "category": category,
                "query": query_text[:100],
                "status": "timeout",
                "latency_ms": 30000
            }
        
        except Exception as e:
            return {
                "id": query_id,
                "category": category,
                "query": query_text[:100],
                "status": "error",
                "error": str(e),
                "latency_ms": int((time.time() - start) * 1000)
            }
    
    def run_test_batch(self, queries: List[Tuple[Dict, str]], batch_num: int, total_batches: int):
        """Run a batch of queries in parallel."""
        print(f"Running batch {batch_num}/{total_batches} ({len(queries)} queries)...")
        
        with ThreadPoolExecutor(max_workers=self.batch_size) as executor:
            futures = []
            for query_data, category in queries:
                future = executor.submit(self.run_single_query, query_data, category)
                futures.append(future)
            
            for future in as_completed(futures):
                result = future.result()
                self.test_results.append(result)
                
                # Print progress
                if result["status"] == "success":
                    print(f"  ✓ {result['id']}: {result['latency_ms']}ms")
                elif result["status"] == "timeout":
                    print(f"  ⏱ {result['id']}: TIMEOUT")
                else:
                    print(f"  ✗ {result['id']}: {result.get('error', 'ERROR')}")
    
    def run_all_tests(self, test_sets: Dict[str, List[Dict]]):
        """Run all test queries in batches."""
        self.start_time = datetime.now()
        print(f"\n{'='*70}")
        print(f"Starting Comprehensive Test Run")
        print(f"Time: {self.start_time}")
        print(f"API: {self.api_url}")
        print(f"{'='*70}\n")
        
        # Flatten all queries with their categories
        all_queries = []
        for category, queries in test_sets.items():
            for query in queries:
                all_queries.append((query, category))
        
        total_queries = len(all_queries)
        print(f"Total queries to run: {total_queries}")
        
        # Run in batches
        batch_size = 10  # Process 10 queries at a time
        batches = [all_queries[i:i+batch_size] for i in range(0, total_queries, batch_size)]
        
        for i, batch in enumerate(batches, 1):
            self.run_test_batch(batch, i, len(batches))
            time.sleep(1)  # Brief pause between batches
        
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds()
        print(f"\n{'='*70}")
        print(f"Test run completed in {duration:.2f} seconds")
        print(f"{'='*70}\n")
    
    def calculate_metrics(self) -> Dict[str, Any]:
        """Calculate aggregate metrics from test results."""
        successful = [r for r in self.test_results if r["status"] == "success"]
        
        if not successful:
            return {"error": "No successful queries"}
        
        latencies = [r["latency_ms"] for r in successful]
        latencies.sort()
        
        # Calculate gate metrics
        median_latency = latencies[len(latencies) // 2] if latencies else 0
        p95_latency = latencies[int(len(latencies) * 0.95)] if latencies else 0
        p99_latency = latencies[int(len(latencies) * 0.99)] if latencies else 0
        
        # Category breakdown
        category_stats = {}
        for category in set(r["category"] for r in self.test_results):
            category_results = [r for r in self.test_results if r["category"] == category]
            category_successful = [r for r in category_results if r["status"] == "success"]
            category_stats[category] = {
                "total": len(category_results),
                "successful": len(category_successful),
                "success_rate": len(category_successful) / len(category_results) if category_results else 0,
                "avg_latency": sum(r["latency_ms"] for r in category_successful) / len(category_successful) if category_successful else 0
            }
        
        return {
            "summary": {
                "total_queries": len(self.test_results),
                "successful": len(successful),
                "failed": len([r for r in self.test_results if r["status"] == "error"]),
                "timeout": len([r for r in self.test_results if r["status"] == "timeout"]),
                "success_rate": len(successful) / len(self.test_results)
            },
            "latency": {
                "min": min(latencies) if latencies else 0,
                "median": median_latency,
                "mean": sum(latencies) / len(latencies) if latencies else 0,
                "p95": p95_latency,
                "p99": p99_latency,
                "max": max(latencies) if latencies else 0
            },
            "by_category": category_stats,
            "gate_values": {
                "latency_median_ms": median_latency,
                "latency_p95_ms": p95_latency,
                "error_rate": 1 - (len(successful) / len(self.test_results)),
                "timeout_rate": len([r for r in self.test_results if r["status"] == "timeout"]) / len(self.test_results)
            }
        }
    
    def generate_html_report(self, metrics: Dict[str, Any]) -> str:
        """Generate an HTML report of test results."""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>AIRI Chatbot Test Report - {self.start_time.strftime('%Y-%m-%d %H:%M')}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #333; }}
                h2 {{ color: #666; border-bottom: 2px solid #ddd; padding-bottom: 5px; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .success {{ color: green; }}
                .error {{ color: red; }}
                .warning {{ color: orange; }}
                .metric-box {{ 
                    display: inline-block; 
                    margin: 10px;
                    padding: 15px;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                }}
                .gate-pass {{ background-color: #d4edda; }}
                .gate-fail {{ background-color: #f8d7da; }}
            </style>
        </head>
        <body>
            <h1>AIRI Chatbot Comprehensive Test Report</h1>
            <p>Generated: {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>Duration: {(self.end_time - self.start_time).total_seconds():.2f} seconds</p>
            
            <h2>Summary</h2>
            <div>
                <div class="metric-box">
                    <strong>Total Queries:</strong> {metrics['summary']['total_queries']}
                </div>
                <div class="metric-box {'' if metrics['summary']['success_rate'] >= 0.95 else 'gate-fail'}">
                    <strong>Success Rate:</strong> {metrics['summary']['success_rate']:.2%}
                </div>
                <div class="metric-box">
                    <strong>Failed:</strong> {metrics['summary']['failed']}
                </div>
                <div class="metric-box">
                    <strong>Timeouts:</strong> {metrics['summary']['timeout']}
                </div>
            </div>
            
            <h2>Latency Metrics</h2>
            <div>
                <div class="metric-box {'' if metrics['latency']['median'] <= 3000 else 'gate-fail'}">
                    <strong>Median:</strong> {metrics['latency']['median']}ms
                </div>
                <div class="metric-box {'' if metrics['latency']['p95'] <= 7000 else 'gate-fail'}">
                    <strong>P95:</strong> {metrics['latency']['p95']}ms
                </div>
                <div class="metric-box">
                    <strong>P99:</strong> {metrics['latency']['p99']}ms
                </div>
            </div>
            
            <h2>Results by Category</h2>
            <table>
                <tr>
                    <th>Category</th>
                    <th>Total</th>
                    <th>Successful</th>
                    <th>Success Rate</th>
                    <th>Avg Latency</th>
                </tr>
        """
        
        for category, stats in metrics['by_category'].items():
            html_content += f"""
                <tr>
                    <td>{category}</td>
                    <td>{stats['total']}</td>
                    <td>{stats['successful']}</td>
                    <td class="{'' if stats['success_rate'] >= 0.9 else 'error'}">{stats['success_rate']:.2%}</td>
                    <td>{stats['avg_latency']:.0f}ms</td>
                </tr>
            """
        
        html_content += """
            </table>
            
            <h2>Deployment Gate Status</h2>
            <ul>
        """
        
        # Check gates
        gates_status = {
            "Median Latency ≤ 3s": metrics['gate_values']['latency_median_ms'] <= 3000,
            "P95 Latency ≤ 7s": metrics['gate_values']['latency_p95_ms'] <= 7000,
            "Error Rate ≤ 5%": metrics['gate_values']['error_rate'] <= 0.05,
            "Timeout Rate ≤ 2%": metrics['gate_values']['timeout_rate'] <= 0.02
        }
        
        for gate, passing in gates_status.items():
            status = "✅ PASS" if passing else "❌ FAIL"
            html_content += f"<li>{gate}: {status}</li>"
        
        html_content += """
            </ul>
        </body>
        </html>
        """
        
        return html_content
    
    def save_results(self, metrics: Dict[str, Any], output_dir: str = "test_results"):
        """Save test results in multiple formats."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save raw results as JSON
        json_file = output_path / f"test_results_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump({
                "metadata": {
                    "start_time": self.start_time.isoformat(),
                    "end_time": self.end_time.isoformat(),
                    "api_url": self.api_url
                },
                "metrics": metrics,
                "results": self.test_results
            }, f, indent=2)
        print(f"JSON results saved to: {json_file}")
        
        # Save summary as CSV
        csv_file = output_path / f"test_summary_{timestamp}.csv"
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Category", "Query", "Status", "Latency (ms)", "Expected Behavior"])
            for result in self.test_results:
                writer.writerow([
                    result.get("id"),
                    result.get("category"),
                    result.get("query", "")[:50],
                    result.get("status"),
                    result.get("latency_ms", ""),
                    result.get("expected_behavior", "")
                ])
        print(f"CSV summary saved to: {csv_file}")
        
        # Save HTML report
        html_file = output_path / f"test_report_{timestamp}.html"
        with open(html_file, 'w') as f:
            f.write(self.generate_html_report(metrics))
        print(f"HTML report saved to: {html_file}")
        
        return {
            "json": str(json_file),
            "csv": str(csv_file),
            "html": str(html_file)
        }


def main():
    parser = argparse.ArgumentParser(description='Run comprehensive chatbot tests')
    parser.add_argument('--api-url', default='http://localhost:5000', help='API URL')
    parser.add_argument('--batch-size', type=int, default=5, help='Parallel query batch size')
    parser.add_argument('--output-dir', default='test_results', help='Output directory')
    parser.add_argument('--categories', nargs='+', help='Specific categories to test')
    
    args = parser.parse_args()
    
    # Create test runner
    runner = ComprehensiveTestRunner(api_url=args.api_url, batch_size=args.batch_size)
    
    # Load test queries
    test_sets = runner.load_test_queries()
    
    # Filter categories if specified
    if args.categories:
        test_sets = {k: v for k, v in test_sets.items() if k in args.categories}
    
    if not test_sets:
        print("No test queries found!")
        sys.exit(1)
    
    # Print test set info
    print("\nTest Sets Loaded:")
    for category, queries in test_sets.items():
        print(f"  - {category}: {len(queries)} queries")
    print(f"  Total: {sum(len(q) for q in test_sets.values())} queries\n")
    
    # Run tests
    runner.run_all_tests(test_sets)
    
    # Calculate metrics
    metrics = runner.calculate_metrics()
    
    # Save results
    saved_files = runner.save_results(metrics, args.output_dir)
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Success Rate: {metrics['summary']['success_rate']:.2%}")
    print(f"Median Latency: {metrics['latency']['median']}ms")
    print(f"P95 Latency: {metrics['latency']['p95']}ms")
    print(f"Error Rate: {metrics['gate_values']['error_rate']:.2%}")
    print("="*70)
    
    # Exit with appropriate code
    if metrics['summary']['success_rate'] >= 0.95:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()