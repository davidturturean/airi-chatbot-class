#!/usr/bin/env python3
"""
Comprehensive test suite for taxonomy query handling with semantic completeness.
Tests 20 queries covering enumeration, comparison, and completeness requirements.
"""

import json
import sys
import datetime
from typing import Dict, List, Any

sys.path.append('.')

from src.core.query.query_intent_analyzer import QueryIntentAnalyzer
from src.core.taxonomy.taxonomy_handler import TaxonomyHandler

def create_test_suite() -> List[Dict[str, Any]]:
    """Create comprehensive test suite for taxonomy completeness."""
    return [
        # Previous failing tests
        {
            'id': 1,
            'category': 'enumeration',
            'query': 'List all 24 subdomains organized by domain',
            'expected_completeness': 0.9,
            'expected_elements': ['Discrimination & bias', 'Privacy violations', 'Fraud & deception', 
                                 'Overreliance on AI', 'Environmental impacts', 'Performance issues', 
                                 'Existential risks'],
            'description': 'Should list ALL 24 subdomains, not just domain names'
        },
        {
            'id': 2,
            'category': 'comparison',
            'query': "What's the difference between intentional and unintentional risks?",
            'expected_completeness': 0.4,
            'expected_elements': ['Intentional', 'Unintentional', 'expected outcome', 
                                 'unexpected outcome', '34%', '35%'],
            'description': 'Should explain both concepts with statistics'
        },
        
        # Completeness tests (requiring exhaustive responses)
        {
            'id': 3,
            'category': 'enumeration',
            'query': 'Show me every domain in the AI risk taxonomy',
            'expected_completeness': 0.8,
            'expected_elements': ['Discrimination & Toxicity', 'Privacy & Security', 'Misinformation',
                                 'Malicious Actors', 'Human-Computer Interaction', 'Socioeconomic',
                                 'AI System Safety'],
            'description': 'Should list all 7 domains with details'
        },
        {
            'id': 4,
            'category': 'enumeration',
            'query': 'What are all the subdomains under Privacy & Security?',
            'expected_completeness': 0.7,
            'expected_elements': ['Privacy violations', 'Security vulnerabilities', 'Data leaks'],
            'description': 'Should list all subdomains for specific domain'
        },
        {
            'id': 5,
            'category': 'statistics',
            'query': 'Give me complete statistics for all risk categories',
            'expected_completeness': 0.8,
            'expected_elements': ['16.2%', '15.8%', '12.4%', '11.6%', '14.9%', '13.5%', '15.6%'],
            'description': 'Should provide all percentage statistics'
        },
        
        # Comparison tests
        {
            'id': 6,
            'category': 'comparison',
            'query': 'Compare pre-deployment vs post-deployment risks',
            'expected_completeness': 0.5,
            'expected_elements': ['Pre-deployment', '13%', 'Post-deployment', '62%'],
            'description': 'Should compare timing categories with stats'
        },
        {
            'id': 7,
            'category': 'comparison', 
            'query': 'What is the difference between human and AI caused risks?',
            'expected_completeness': 0.5,
            'expected_elements': ['Human', '39%', 'AI', '41%'],
            'description': 'Should compare entity types with percentages'
        },
        {
            'id': 8,
            'category': 'comparison',
            'query': 'Compare the causal taxonomy with the domain taxonomy',
            'expected_completeness': 0.5,
            'expected_elements': ['Causal', 'Entity', 'Domain', '7 domains', '24 subdomains'],
            'description': 'Should explain both taxonomy systems'
        },
        
        # Specific enumeration tests
        {
            'id': 9,
            'category': 'enumeration',
            'query': 'List the 3 dimensions of the causal taxonomy',
            'expected_completeness': 0.7,
            'expected_elements': ['Entity', 'Intentionality', 'Timing'],
            'description': 'Should list all 3 causal dimensions'
        },
        {
            'id': 10,
            'category': 'enumeration',
            'query': 'Show all subdomains related to AI System Safety',
            'expected_completeness': 0.7,
            'expected_elements': ['Performance issues', 'Safety & alignment', 'transparency',
                                 'Weaponization', 'Existential risks'],
            'description': 'Should list all 6 subdomains for domain 7'
        },
        
        # Mixed intent tests
        {
            'id': 11,
            'category': 'mixed',
            'query': 'What are the main risk categories in the AI Risk Database v3?',
            'expected_completeness': 0.6,
            'expected_elements': ['Causal Taxonomy', 'Domain Taxonomy', '7 domains'],
            'description': 'Should provide overview of both taxonomies'
        },
        {
            'id': 12,
            'category': 'mixed',
            'query': 'Explain the complete structure of AI risk categorization',
            'expected_completeness': 0.8,
            'expected_elements': ['Causal', 'Domain', '7 domains', '24 subdomains', 'Entity'],
            'description': 'Should provide comprehensive taxonomy overview'
        },
        
        # Detail-requiring queries
        {
            'id': 13,
            'category': 'detail',
            'query': 'Provide full details about the Discrimination & Toxicity domain',
            'expected_completeness': 0.8,
            'expected_elements': ['16.2%', 'Discrimination & bias', 'toxic content', 'Aggression'],
            'description': 'Should provide complete domain details'
        },
        {
            'id': 14,
            'category': 'detail',
            'query': 'Give me all information about timing in the causal taxonomy',
            'expected_completeness': 0.8,
            'expected_elements': ['Pre-deployment', '13%', 'Post-deployment', '62%', 'Other', '25%'],
            'description': 'Should provide all timing details and stats'
        },
        
        # Counting/statistical queries
        {
            'id': 15,
            'category': 'statistics',
            'query': 'How many risks are in each of the 7 domains?',
            'expected_completeness': 0.7,
            'expected_elements': ['16.2%', '15.8%', '12.4%', '11.6%', '14.9%', '13.5%', '15.6%'],
            'description': 'Should list percentages for all domains'
        },
        {
            'id': 16,
            'category': 'statistics',
            'query': 'What percentage of risks fall into each causal category?',
            'expected_completeness': 0.7,
            'expected_elements': ['39%', '41%', '34%', '35%', '13%', '62%'],
            'description': 'Should provide all causal taxonomy statistics'
        },
        
        # Natural language variations
        {
            'id': 17,
            'category': 'natural',
            'query': 'Tell me everything about how AI risks are organized',
            'expected_completeness': 0.7,
            'expected_elements': ['Causal', 'Domain', 'taxonomy', '7 domains', '24 subdomains'],
            'description': 'Should provide comprehensive taxonomy explanation'
        },
        {
            'id': 18,
            'category': 'natural',
            'query': 'I need a complete list of all risk subcategories',
            'expected_completeness': 0.9,
            'expected_elements': ['Discrimination & bias', 'Privacy violations', 'Fraud & deception',
                                 'Performance issues', 'Environmental impacts'],
            'description': 'Should list all 24 subdomains'
        },
        
        # Edge cases
        {
            'id': 19,
            'category': 'edge',
            'query': 'Show the full breakdown of unintentional AI-caused post-deployment risks',
            'expected_completeness': 0.6,
            'expected_elements': ['Unintentional', 'AI', 'Post-deployment'],
            'description': 'Should handle complex multi-dimensional query'
        },
        {
            'id': 20,
            'category': 'edge',
            'query': 'List every single subdomain across all 7 domains with their percentages',
            'expected_completeness': 1.0,
            'expected_elements': ['24', 'Discrimination & bias', 'Existential risks', '16.2%', '15.6%'],
            'description': 'Should provide exhaustive enumeration with statistics'
        }
    ]

def test_query(query: str, test_info: Dict[str, Any], 
               intent_analyzer: QueryIntentAnalyzer, 
               taxonomy_handler: TaxonomyHandler) -> Dict[str, Any]:
    """Test a single query and return results."""
    
    # Analyze intent
    intent = intent_analyzer.analyze_query(query)
    
    # Get taxonomy response
    try:
        response = taxonomy_handler.handle_taxonomy_query(query)
        response_text = response.content
        
        # Check for expected elements
        missing_elements = []
        found_elements = []
        for element in test_info['expected_elements']:
            if element.lower() in response_text.lower():
                found_elements.append(element)
            else:
                missing_elements.append(element)
        
        # Calculate success metrics
        coverage = len(found_elements) / len(test_info['expected_elements'])
        passed = coverage >= 0.8  # 80% of expected elements found
        
        # Determine if completeness expectation was met
        completeness_met = (
            (intent.completeness_level >= test_info['expected_completeness'] - 0.1) or
            (intent.completeness_level >= 0.7 and test_info['expected_completeness'] >= 0.7)
        )
        
        return {
            'test_id': test_info['id'],
            'category': test_info['category'],
            'query': query,
            'description': test_info['description'],
            'intent_analysis': {
                'completeness_level': round(intent.completeness_level, 2),
                'expected_completeness': test_info['expected_completeness'],
                'completeness_met': completeness_met,
                'query_type': intent.query_type,
                'enumeration_mode': intent.enumeration_mode,
                'comparison_mode': intent.comparison_mode,
                'concepts_mentioned': intent.concepts_mentioned[:5] if intent.concepts_mentioned else [],
                'detail_level': intent_analyzer.get_response_detail_level(intent)
            },
            'response': {
                'length': len(response_text),
                'preview': response_text[:500] + '...' if len(response_text) > 500 else response_text,
                'full_text': response_text
            },
            'validation': {
                'passed': passed,
                'coverage': round(coverage, 2),
                'expected_elements': test_info['expected_elements'],
                'found_elements': found_elements,
                'missing_elements': missing_elements
            }
        }
    except Exception as e:
        return {
            'test_id': test_info['id'],
            'category': test_info['category'],
            'query': query,
            'description': test_info['description'],
            'error': str(e),
            'passed': False
        }

def main():
    """Run comprehensive taxonomy test suite."""
    
    print("=" * 80)
    print("COMPREHENSIVE TAXONOMY COMPLETENESS TEST SUITE")
    print("=" * 80)
    print(f"Testing semantic understanding of completeness requirements")
    print(f"Date: {datetime.datetime.now().isoformat()}")
    print()
    
    # Initialize components
    intent_analyzer = QueryIntentAnalyzer()
    taxonomy_handler = TaxonomyHandler()
    
    # Get test suite
    test_suite = create_test_suite()
    
    # Run tests
    results = []
    passed_count = 0
    
    for test_info in test_suite:
        print(f"\nTest {test_info['id']}/{len(test_suite)}: {test_info['category'].upper()}")
        print(f"Query: \"{test_info['query']}\"")
        
        result = test_query(test_info['query'], test_info, intent_analyzer, taxonomy_handler)
        results.append(result)
        
        if result.get('validation', {}).get('passed', False):
            passed_count += 1
            print(f"✓ PASSED (coverage: {result['validation']['coverage']*100:.0f}%)")
        else:
            print(f"✗ FAILED", end="")
            if 'error' in result:
                print(f" - Error: {result['error']}")
            else:
                print(f" - Coverage: {result.get('validation', {}).get('coverage', 0)*100:.0f}%")
                missing = result.get('validation', {}).get('missing_elements', [])
                if missing:
                    print(f"  Missing: {', '.join(missing[:3])}", end="")
                    if len(missing) > 3:
                        print(f" and {len(missing)-3} more")
                    else:
                        print()
    
    # Summary statistics
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    total = len(results)
    pass_rate = (passed_count / total) * 100
    
    print(f"Overall Pass Rate: {passed_count}/{total} ({pass_rate:.1f}%)")
    
    # Category breakdown
    categories = {}
    for result in results:
        cat = result['category']
        if cat not in categories:
            categories[cat] = {'total': 0, 'passed': 0}
        categories[cat]['total'] += 1
        if result.get('validation', {}).get('passed', False):
            categories[cat]['passed'] += 1
    
    print("\nBy Category:")
    for cat, stats in sorted(categories.items()):
        cat_rate = (stats['passed'] / stats['total']) * 100
        print(f"  {cat.capitalize():12} {stats['passed']}/{stats['total']} ({cat_rate:.0f}%)")
    
    # Completeness analysis
    completeness_met_count = sum(1 for r in results 
                                 if r.get('intent_analysis', {}).get('completeness_met', False))
    print(f"\nCompleteness Detection: {completeness_met_count}/{total} queries correctly analyzed")
    
    # Save detailed results
    output_file = 'taxonomy_test_results_comprehensive.json'
    with open(output_file, 'w') as f:
        json.dump({
            'metadata': {
                'date': datetime.datetime.now().isoformat(),
                'total_tests': total,
                'passed': passed_count,
                'pass_rate': pass_rate,
                'categories': categories
            },
            'results': results
        }, f, indent=2)
    
    print(f"\nDetailed results saved to: {output_file}")
    
    # Save summary for quick reference
    summary_file = 'taxonomy_test_summary.json'
    summary = []
    for r in results:
        summary.append({
            'id': r['test_id'],
            'query': r['query'],
            'passed': r.get('validation', {}).get('passed', False),
            'coverage': r.get('validation', {}).get('coverage', 0),
            'completeness_level': r.get('intent_analysis', {}).get('completeness_level', 0),
            'response_length': r.get('response', {}).get('length', 0)
        })
    
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"Summary saved to: {summary_file}")
    
    return pass_rate >= 80  # Success if 80% or more tests pass

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)