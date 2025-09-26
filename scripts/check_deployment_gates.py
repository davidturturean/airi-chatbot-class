#!/usr/bin/env python3
"""
Check deployment gates for the AIRI chatbot based on PI's Running Lean criteria.
This script evaluates if the chatbot is ready for the next deployment stage.
"""
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import requests
from tabulate import tabulate

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.services.metrics_service import metrics_service


def check_local_gates(hours: int = 24) -> Dict[str, Any]:
    """Check deployment gates using local metrics."""
    return metrics_service.check_deployment_gates(hours)


def check_remote_gates(api_url: str, hours: int = 24) -> Dict[str, Any]:
    """Check deployment gates via API endpoint."""
    try:
        response = requests.get(f"{api_url}/api/metrics/gates", params={"hours": hours})
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching remote gates: {e}")
        return None


def format_gate_status(gate_name: str, gate_data: Dict[str, Any]) -> str:
    """Format gate status with visual indicators."""
    icon = "✅" if gate_data["passing"] else "❌"
    value = gate_data["value"]
    threshold = gate_data["threshold"]
    
    # Format numbers nicely
    if isinstance(value, float):
        if value < 1:
            value_str = f"{value:.2%}"
        else:
            value_str = f"{value:.2f}"
    else:
        value_str = str(value)
    
    if isinstance(threshold, float):
        if threshold < 1:
            threshold_str = f"{threshold:.2%}"
        else:
            threshold_str = f"{threshold:.2f}"
    else:
        threshold_str = str(threshold)
    
    return f"{icon} {value_str} (target: {threshold_str})"


def print_gates_report(gates_status: Dict[str, Any], verbose: bool = False):
    """Print a formatted gates report."""
    print("\n" + "="*70)
    print("🚀 DEPLOYMENT READINESS ASSESSMENT")
    print("="*70)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if gates_status and 'gates_passing' in gates_status:
        print(f"Gates Passing: {gates_status['gates_passing']}/{gates_status['gates_total']}")
    print()
    
    # Overall status
    if gates_status and 'ready' in gates_status:
        if gates_status['ready']:
            print("✅ READY FOR DEPLOYMENT")
        else:
            print("⚠️  NOT READY FOR DEPLOYMENT")
        
        if 'recommendation' in gates_status:
            print(f"Recommendation: {gates_status['recommendation']}")
    else:
        print("⚠️  No metrics data available yet")
        print("Start using the chatbot to generate metrics")
    print()
    
    # Gates table
    if gates_status and 'gates' in gates_status:
        table_data = []
        for gate_name, gate_data in gates_status['gates'].items():
            table_data.append([
                gate_name.replace('_', ' ').title(),
                format_gate_status(gate_name, gate_data),
                "✅ Pass" if gate_data['passing'] else "❌ Fail"
            ])
        
        if table_data:
            print(tabulate(table_data, 
                           headers=["Gate", "Current vs Target", "Status"],
                           tablefmt="grid"))
    
    # Detailed breakdown if verbose
    if verbose and gates_status and 'gates' in gates_status:
        print("\n" + "="*70)
        print("DETAILED GATE INFORMATION")
        print("="*70)
        
        for gate_name, gate_data in gates_status['gates'].items():
            print(f"\n{gate_name.replace('_', ' ').upper()}:")
            print(f"  Current Value: {gate_data['value']}")
            print(f"  Target: {gate_data['threshold']}")
            print(f"  Status: {'PASSING' if gate_data['passing'] else 'FAILING'}")
            
            # Add specific recommendations for failing gates
            if not gate_data['passing']:
                print(f"  ⚠️  Action Required: {get_gate_recommendation(gate_name, gate_data)}")
    
    # Next steps
    print("\n" + "="*70)
    print("NEXT STEPS")
    print("="*70)
    
    gates_passing = gates_status.get('gates_passing', 0) if gates_status else 0
    if gates_passing >= 10:
        print("🎉 All gates passing! Ready for full deployment.")
        print("1. Create deployment announcement")
        print("2. Remove password protection")
        print("3. Monitor initial traffic closely")
    elif gates_passing >= 8:
        print("✅ Ready for canary deployment (5-10% traffic)")
        print("1. Fix remaining issues")
        print("2. Set up canary routing")
        print("3. Monitor metrics for 2 weeks")
    elif gates_passing >= 6:
        print("🔄 Ready for expanded beta testing")
        print("1. Address critical failing gates")
        print("2. Recruit more beta testers")
        print("3. Gather additional feedback")
    else:
        print("⚠️  Continue internal testing and optimization")
        print("1. Focus on critical performance issues")
        print("2. Improve accuracy and response times")
        print("3. Run more comprehensive tests")


def get_gate_recommendation(gate_name: str, gate_data: Dict[str, Any]) -> str:
    """Get specific recommendations for failing gates."""
    recommendations = {
        "groundedness": "Review prompt engineering and retrieval quality",
        "hallucination_rate": "Implement stricter fact-checking and validation",
        "retrieval_hit_rate": "Optimize vector embeddings and search parameters",
        "latency_median": "Optimize query processing and caching",
        "latency_p95": "Investigate slow queries and add timeouts",
        "containment_rate": "Improve response quality and completeness",
        "satisfaction_score": "Gather user feedback and improve UX",
        "cost_per_query": "Optimize token usage and model selection",
        "safety_violations": "Review and strengthen content filters",
        "freshness_hours": "Set up automated index updates"
    }
    return recommendations.get(gate_name, "Review and optimize this metric")


def export_report(gates_status: Dict[str, Any], output_file: str):
    """Export gates report to file."""
    report = {
        "timestamp": datetime.now().isoformat(),
        "gates_status": gates_status,
        "summary": {
            "ready_for_deployment": gates_status['ready'],
            "gates_passing": gates_status['gates_passing'],
            "gates_total": gates_status['gates_total'],
            "recommendation": gates_status['recommendation']
        }
    }
    
    output_path = Path(output_file)
    
    if output_path.suffix == '.json':
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
    elif output_path.suffix == '.csv':
        import csv
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Gate', 'Current Value', 'Target', 'Status'])
            for gate_name, gate_data in gates_status['gates'].items():
                writer.writerow([
                    gate_name,
                    gate_data['value'],
                    gate_data['threshold'],
                    'Pass' if gate_data['passing'] else 'Fail'
                ])
    else:
        # Default to text format
        with open(output_path, 'w') as f:
            f.write(f"Deployment Gates Report - {datetime.now()}\n")
            f.write("="*50 + "\n\n")
            f.write(f"Ready for Deployment: {gates_status['ready']}\n")
            f.write(f"Gates Passing: {gates_status['gates_passing']}/{gates_status['gates_total']}\n")
            f.write(f"Recommendation: {gates_status['recommendation']}\n\n")
            
            for gate_name, gate_data in gates_status['gates'].items():
                f.write(f"{gate_name}: {gate_data['value']} (target: {gate_data['threshold']}) - ")
                f.write("PASS\n" if gate_data['passing'] else "FAIL\n")
    
    print(f"\nReport exported to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Check deployment gates for AIRI chatbot')
    parser.add_argument('--hours', type=int, default=24, help='Number of hours to analyze (default: 24)')
    parser.add_argument('--api-url', help='API URL for remote checking (optional)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--export', help='Export report to file (json, csv, or txt)')
    parser.add_argument('--watch', action='store_true', help='Watch mode - check every 5 minutes')
    
    args = parser.parse_args()
    
    if args.watch:
        import time
        print("Starting watch mode - checking gates every 5 minutes")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                # Clear screen (works on Unix/Mac)
                import os
                os.system('clear')
                
                # Check gates
                if args.api_url:
                    gates_status = check_remote_gates(args.api_url, args.hours)
                else:
                    gates_status = check_local_gates(args.hours)
                
                if gates_status:
                    print_gates_report(gates_status, args.verbose)
                
                # Wait 5 minutes
                print("\nNext check in 5 minutes... (Ctrl+C to stop)")
                time.sleep(300)
                
        except KeyboardInterrupt:
            print("\nWatch mode stopped")
            return
    else:
        # Single check
        if args.api_url:
            gates_status = check_remote_gates(args.api_url, args.hours)
        else:
            gates_status = check_local_gates(args.hours)
        
        if gates_status:
            print_gates_report(gates_status, args.verbose)
            
            if args.export:
                export_report(gates_status, args.export)
            
            # Exit with appropriate code
            if gates_status and 'ready' in gates_status:
                sys.exit(0 if gates_status['ready'] else 1)
            else:
                sys.exit(1)  # No data available
        else:
            print("Failed to check deployment gates")
            sys.exit(2)


if __name__ == '__main__':
    main()