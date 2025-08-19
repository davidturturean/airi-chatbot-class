#!/usr/bin/env python3
"""
Comprehensive Taxonomy Testing Suite
Tests whether taxonomy responses meet PI's standards for complete, systematic information.

PI Requirements:
1. Complete information (all 7 domains, 24 subdomains)
2. Systematic structure (not summaries)
3. Specific details for both taxonomies
4. Proper citation to preprint
"""

import sys
import os
import json
from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum
from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

# Add project root to path
sys.path.insert(0, '.')

# Set test API key for OpenAI if not set
if not os.environ.get('OPENAI_API_KEY'):
    os.environ['OPENAI_API_KEY'] = 'test'

from src.core.services.chat_service import ChatService
from src.core.taxonomy.taxonomy_handler import TaxonomyHandler


class TestResult(Enum):
    PASS = "✅ PASS"
    PARTIAL = "⚠️ PARTIAL" 
    FAIL = "❌ FAIL"


@dataclass
class TestCase:
    """Test case for taxonomy queries."""
    id: int
    category: str
    query: str
    expected_elements: List[str]
    check_structure: bool = True
    check_completeness: bool = True


class TaxonomyTester:
    """Tests taxonomy responses against PI standards."""
    
    def __init__(self):
        self.chat_service = ChatService()
        self.taxonomy_handler = TaxonomyHandler()
        self.test_results = []
        
        # Expected elements for validation
        self.all_7_domains = [
            "Discrimination & Toxicity",
            "Privacy & Security", 
            "Misinformation",
            "Malicious Actors & Misuse",
            "Human-Computer Interaction",
            "Socioeconomic & Environmental",
            "AI System Safety, Failures, & Limitations"
        ]
        
        self.causal_elements = [
            "Entity", "Human", "AI",
            "Intentionality", "Intentional", "Unintentional",
            "Timing", "Pre-deployment", "Post-deployment"
        ]
        
        self.test_cases = self._create_test_cases()
    
    def _create_test_cases(self) -> List[TestCase]:
        """Create comprehensive test cases based on PI requirements."""
        return [
            # Category A: Causal Taxonomy Tests
            TestCase(
                id=1,
                category="Causal Taxonomy",
                query="What is the Causal Taxonomy of AI in the repository?",
                expected_elements=self.causal_elements
            ),
            TestCase(
                id=2,
                category="Causal Taxonomy",
                query="Explain the Entity × Intent × Timing framework",
                expected_elements=self.causal_elements
            ),
            TestCase(
                id=3,
                category="Causal Taxonomy",
                query="What percentage of risks are human vs AI caused?",
                expected_elements=["39%", "41%", "Human", "AI", "Entity"]
            ),
            
            # Category B: Domain Taxonomy Tests
            TestCase(
                id=4,
                category="Domain Taxonomy",
                query="What are the 7 domains in the AI Risk Repository?",
                expected_elements=self.all_7_domains + ["24 subdomain"]
            ),
            TestCase(
                id=5,
                category="Domain Taxonomy",
                query="List all 24 subdomains organized by domain",
                expected_elements=self.all_7_domains + [
                    "Discrimination & bias",
                    "Privacy violations",
                    "Fraud & deception",
                    "Overreliance on AI",
                    "Environmental impacts",
                    "Performance issues",
                    "Existential risks"
                ]
            ),
            TestCase(
                id=6,
                category="Domain Taxonomy",
                query="What is domain 3 about?",
                expected_elements=["Misinformation", "false", "misleading", "harmful information"]
            ),
            
            # Category C: Combined/General Tests
            TestCase(
                id=7,
                category="Combined",
                query="What are the main risk categories in the AI Risk Database v3?",
                expected_elements=self.all_7_domains + ["Causal Taxonomy", "Domain Taxonomy"]
            ),
            TestCase(
                id=8,
                category="Combined",
                query="Describe the taxonomy structure of the repository",
                expected_elements=["Causal", "Domain", "7 domains", "24 subdomains", "Entity", "Timing"]
            ),
            TestCase(
                id=9,
                category="Combined",
                query="How does the repository categorize AI risks?",
                expected_elements=["two", "taxonomies", "Causal", "Domain"] + self.all_7_domains[:3]
            ),
            
            # Category D: Edge Cases
            TestCase(
                id=10,
                category="Edge Case",
                query="Tell me about privacy and security risks",
                expected_elements=["Privacy & Security", "domain", "15.8%", "violations", "vulnerabilities"]
            ),
            TestCase(
                id=11,
                category="Edge Case",
                query="What's the difference between intentional and unintentional risks?",
                expected_elements=["Intentional", "Unintentional", "expected outcome", "unexpected outcome", "34%", "35%"]
            ),
            TestCase(
                id=12,
                category="Edge Case",
                query="How many risks are in each domain?",
                expected_elements=["16.2%", "15.8%", "12.4%", "11.6%", "14.9%", "13.5%", "15.6%"]
            )
        ]
    
    def run_test(self, test_case: TestCase) -> Dict:
        """Run a single test case and evaluate the response."""
        print(f"\n{'='*70}")
        print(f"Test #{test_case.id}: {test_case.category}")
        print(f"Query: {test_case.query}")
        print("-" * 70)
        
        try:
            # Get response from chat service
            response, sources, _ = self.chat_service.process_query(
                test_case.query, 
                f"test-{test_case.id}", 
                "test-session"
            )
            
            # Evaluate response
            evaluation = self._evaluate_response(response, test_case)
            
            # Print results
            print(f"\nResponse Preview (first 800 chars):")
            print(response[:800])
            print(f"\n{evaluation['result'].value}: {evaluation['summary']}")
            
            if evaluation['missing_elements']:
                print(f"Missing elements: {', '.join(evaluation['missing_elements'][:5])}")
            
            return {
                'test_id': test_case.id,
                'category': test_case.category,
                'query': test_case.query,
                'response_length': len(response),
                'evaluation': evaluation,
                'response': response
            }
            
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            return {
                'test_id': test_case.id,
                'category': test_case.category,
                'query': test_case.query,
                'error': str(e),
                'evaluation': {
                    'result': TestResult.FAIL,
                    'summary': f"Error occurred: {str(e)}"
                }
            }
    
    def _evaluate_response(self, response: str, test_case: TestCase) -> Dict:
        """Evaluate if response meets PI standards."""
        evaluation = {
            'result': TestResult.PASS,
            'summary': '',
            'missing_elements': [],
            'has_structure': False,
            'has_citation': False,
            'is_complete': False
        }
        
        # Check for expected elements
        missing = []
        for element in test_case.expected_elements:
            if element not in response:
                missing.append(element)
        
        evaluation['missing_elements'] = missing
        
        # Check structure (headings, formatting)
        has_headings = any(marker in response for marker in ['##', '###', '**', '1.', '2.'])
        has_categories = 'domain' in response.lower() or 'taxonomy' in response.lower()
        evaluation['has_structure'] = has_headings and has_categories
        
        # Check citation
        evaluation['has_citation'] = 'Slattery' in response or 'preprint' in response.lower()
        
        # Check completeness
        if test_case.check_completeness:
            if 'domain' in test_case.category.lower():
                # For domain queries, must have all 7 domains
                evaluation['is_complete'] = all(domain in response for domain in self.all_7_domains)
            elif 'causal' in test_case.category.lower():
                # For causal queries, must have all 3 dimensions
                evaluation['is_complete'] = all(
                    elem in response for elem in ['Entity', 'Intentionality', 'Timing']
                )
            else:
                evaluation['is_complete'] = len(missing) == 0
        
        # Determine overall result
        if len(missing) == 0 and evaluation['has_structure'] and evaluation['has_citation']:
            evaluation['result'] = TestResult.PASS
            evaluation['summary'] = "Meets all PI standards"
        elif len(missing) <= 2 or (evaluation['has_structure'] and len(missing) <= 4):
            evaluation['result'] = TestResult.PARTIAL
            evaluation['summary'] = f"Partially meets standards (missing {len(missing)} elements)"
        else:
            evaluation['result'] = TestResult.FAIL
            evaluation['summary'] = f"Does not meet PI standards (missing {len(missing)} elements)"
        
        # Special check for summary-like responses
        if len(response) < 500 and 'domain' in test_case.category.lower():
            evaluation['result'] = TestResult.FAIL
            evaluation['summary'] = "Response too short - appears to be a summary"
        
        return evaluation
    
    def run_all_tests(self) -> None:
        """Run all test cases and generate report."""
        print("\n" + "="*70)
        print("COMPREHENSIVE TAXONOMY TESTING SUITE")
        print("Testing against PI Standards for Complete, Systematic Responses")
        print("="*70)
        
        results = []
        for test_case in self.test_cases:
            result = self.run_test(test_case)
            results.append(result)
        
        self.generate_report(results)
    
    def generate_report(self, results: List[Dict]) -> None:
        """Generate comprehensive assessment report."""
        print("\n" + "="*70)
        print("FINAL ASSESSMENT REPORT")
        print("="*70)
        
        # Count results by type
        pass_count = sum(1 for r in results if r['evaluation']['result'] == TestResult.PASS)
        partial_count = sum(1 for r in results if r['evaluation']['result'] == TestResult.PARTIAL)
        fail_count = sum(1 for r in results if r['evaluation']['result'] == TestResult.FAIL)
        
        print(f"\n📊 Overall Results:")
        print(f"  ✅ PASS: {pass_count}/{len(results)} ({pass_count*100//len(results)}%)")
        print(f"  ⚠️ PARTIAL: {partial_count}/{len(results)} ({partial_count*100//len(results)}%)")
        print(f"  ❌ FAIL: {fail_count}/{len(results)} ({fail_count*100//len(results)}%)")
        
        # Results by category
        print(f"\n📋 Results by Category:")
        categories = {}
        for r in results:
            cat = r['category']
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(r['evaluation']['result'])
        
        for cat, res_list in categories.items():
            pass_cat = sum(1 for r in res_list if r == TestResult.PASS)
            print(f"  {cat}: {pass_cat}/{len(res_list)} passed")
        
        # Common issues
        print(f"\n⚠️ Common Issues Found:")
        all_missing = []
        for r in results:
            if 'evaluation' in r and 'missing_elements' in r['evaluation']:
                all_missing.extend(r['evaluation']['missing_elements'])
        
        if all_missing:
            from collections import Counter
            missing_counts = Counter(all_missing)
            for element, count in missing_counts.most_common(5):
                print(f"  - '{element}' missing in {count} responses")
        else:
            print("  No systematic missing elements found")
        
        # PI Standards Assessment
        print(f"\n🎯 PI Standards Compliance:")
        print(f"  1. Complete Information: {'✅' if pass_count > 8 else '⚠️' if pass_count > 5 else '❌'}")
        print(f"  2. Systematic Structure: {'✅' if all(r['evaluation'].get('has_structure', False) for r in results[:5]) else '❌'}")
        print(f"  3. Proper Citations: {'✅' if all(r['evaluation'].get('has_citation', False) for r in results[:5]) else '❌'}")
        print(f"  4. Not Summary-Like: {'✅' if all(len(r.get('response', '')) > 500 for r in results[:5]) else '❌'}")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        if fail_count > 0:
            print("  - Some queries still need improvement to meet PI standards")
            print("  - Consider enhancing detection patterns for edge cases")
        if partial_count > 3:
            print("  - Several responses are incomplete - check element extraction")
        if pass_count == len(results):
            print("  - System fully meets PI standards! 🎉")
        
        # Save detailed results
        with open('taxonomy_test_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n📁 Detailed results saved to taxonomy_test_results.json")


if __name__ == "__main__":
    tester = TaxonomyTester()
    tester.run_all_tests()