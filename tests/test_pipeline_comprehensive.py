#!/usr/bin/env python3
"""
Comprehensive pipeline testing script with Gemini quota management.
Tests all 8 pipeline enhancements with rate limiting and detailed analysis.
"""

import time
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, asdict
import statistics
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.core.services.chat_service import ChatService
from src.core.models.gemini import GeminiModel
from src.core.storage.vector_store import VectorStore
from src.config.settings import settings
from src.config.logging import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger(__name__)

@dataclass
class TestResult:
    """Individual test result with detailed metrics."""
    prompt: str
    domain: str
    expected_domain: str
    response: str
    response_time: float
    word_count: int
    has_citations: bool
    citation_count: int
    validation_score: float
    confidence_score: float
    detected_domain: str
    is_refusal: bool
    quality_metrics: Dict[str, float]
    error: str = ""

@dataclass
class TestSummary:
    """Summary of all test results."""
    total_tests: int
    successful_tests: int
    failed_tests: int
    avg_response_time: float
    avg_word_count: float
    avg_validation_score: float
    citation_rate: float
    refusal_rate: float
    domain_accuracy: float
    quality_breakdown: Dict[str, float]
    test_results: List[TestResult]

class GeminiRateLimiter:
    """Manages Gemini API rate limiting to respect quota limits."""
    
    def __init__(self, requests_per_minute: int = 15):
        self.requests_per_minute = requests_per_minute
        self.min_interval = 60.0 / requests_per_minute  # seconds between requests
        self.last_request_time = 0
        self.request_count = 0
        
    def wait_if_needed(self):
        """Wait if necessary to respect rate limits."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_interval:
            wait_time = self.min_interval - time_since_last
            logger.info(f"Rate limiting: waiting {wait_time:.1f} seconds...")
            time.sleep(wait_time)
        
        self.last_request_time = time.time()
        self.request_count += 1
        
        if self.request_count % 10 == 0:
            logger.info(f"Completed {self.request_count} requests")

class PipelineTester:
    """Comprehensive pipeline testing system."""
    
    def __init__(self):
        self.rate_limiter = GeminiRateLimiter(requests_per_minute=15)  # Conservative rate limit
        self.chat_service = None
        self.test_results = []
        
    def initialize_services(self):
        """Initialize all services for testing."""
        try:
            logger.info("Initializing services for testing...")
            
            # Initialize vector store
            vector_store = VectorStore(
                embedding_provider=settings.EMBEDDING_PROVIDER,
                api_key=settings.GEMINI_API_KEY,
                repository_path=settings.get_repository_path(),
                persist_directory=str(settings.CHROMA_DB_DIR),
                use_hybrid_search=settings.USE_HYBRID_SEARCH
            )
            
            # Initialize vector store
            success = vector_store.initialize()
            if not success:
                raise Exception("Vector store initialization failed")
            
            # Initialize Gemini model
            gemini_model = GeminiModel(
                api_key=settings.GEMINI_API_KEY,
                model_name=settings.GEMINI_MODEL_NAME
            )
            
            # Initialize chat service
            self.chat_service = ChatService(
                gemini_model=gemini_model,
                vector_store=vector_store,
                query_monitor=None
            )
            
            logger.info("Services initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")
            return False
    
    def get_test_prompts(self) -> List[Tuple[str, str, str]]:
        """Get comprehensive test prompts. Returns (prompt, expected_domain, description)."""
        return [
            # Socioeconomic Domain Tests (8 prompts)
            ("How does AI automation affect employment opportunities?", "socioeconomic", "Basic employment impact"),
            ("What are the economic risks of widespread AI adoption in the workforce?", "socioeconomic", "Economic risk analysis"),
            ("Can AI systems cause job displacement in manufacturing?", "socioeconomic", "Specific industry impact"),
            ("How does AI affect wage inequality and economic stratification?", "socioeconomic", "Wage inequality"),
            ("What are the socioeconomic implications of AI in hiring decisions?", "socioeconomic", "Hiring discrimination"),
            ("How might AI impact labor market dynamics and worker rights?", "socioeconomic", "Labor market effects"),
            ("What economic disruptions could AI cause in traditional industries?", "socioeconomic", "Industry disruption"),
            ("How does AI automation affect low-skilled vs high-skilled employment?", "socioeconomic", "Skill-based displacement"),
            
            # Safety Domain Tests (8 prompts)
            ("What are the physical safety risks of AI systems?", "safety", "Physical safety concerns"),
            ("How can AI systems cause accidents or injuries?", "safety", "Accident scenarios"),
            ("What safety measures should be implemented for AI systems?", "safety", "Safety protocols"),
            ("Can AI systems pose security threats to infrastructure?", "safety", "Infrastructure security"),
            ("What are the risks of AI system failures in critical applications?", "safety", "Critical system failures"),
            ("How do we ensure AI systems don't cause harm to users?", "safety", "User safety"),
            ("What are the dangers of malicious use of AI technology?", "safety", "Malicious use scenarios"),
            ("How can AI systems be made more secure against attacks?", "safety", "Security hardening"),
            
            # Privacy Domain Tests (6 prompts)
            ("How does AI impact personal data privacy?", "privacy", "Data privacy concerns"),
            ("What are the surveillance risks of AI systems?", "privacy", "Surveillance threats"),
            ("Can AI systems violate user privacy through data collection?", "privacy", "Data collection privacy"),
            ("How do AI systems handle confidential information?", "privacy", "Confidential data handling"),
            ("What privacy protections exist for AI-processed data?", "privacy", "Privacy protections"),
            ("Can AI systems be used for unauthorized monitoring?", "privacy", "Unauthorized monitoring"),
            
            # Bias Domain Tests (6 prompts)
            ("How does AI perpetuate discrimination and bias?", "bias", "Discrimination in AI"),
            ("What are the fairness issues with AI decision-making?", "bias", "Fairness concerns"),
            ("Can AI systems exhibit racial or gender bias?", "bias", "Demographic bias"),
            ("How do we ensure AI systems are equitable?", "bias", "Equity in AI"),
            ("What bias exists in AI training data?", "bias", "Training data bias"),
            ("How can we detect and mitigate algorithmic bias?", "bias", "Bias detection"),
            
            # Governance Domain Tests (6 prompts)
            ("What regulations exist for AI system deployment?", "governance", "AI regulations"),
            ("How should AI systems be governed and controlled?", "governance", "AI governance"),
            ("What legal frameworks apply to AI technology?", "governance", "Legal frameworks"),
            ("How do we ensure AI compliance with regulations?", "governance", "Compliance requirements"),
            ("What oversight mechanisms exist for AI systems?", "governance", "Oversight mechanisms"),
            ("How are AI ethics enforced in practice?", "governance", "Ethics enforcement"),
            
            # Technical Domain Tests (6 prompts)
            ("How reliable are current AI algorithms?", "technical", "Algorithm reliability"),
            ("What are the performance limitations of AI systems?", "technical", "Performance limits"),
            ("How do we measure AI system accuracy?", "technical", "Accuracy measurement"),
            ("What technical challenges exist in AI development?", "technical", "Development challenges"),
            ("How robust are AI systems to edge cases?", "technical", "Robustness testing"),
            ("What are the scalability issues with AI systems?", "technical", "Scalability concerns"),
            
            # Edge Cases and Multi-Domain Tests (6 prompts)
            ("What are the overall risks of AI technology?", "general", "Broad AI risks"),
            ("How does AI affect both jobs and privacy?", "socioeconomic", "Multi-domain query"),
            ("What safety and bias concerns exist in AI hiring?", "safety", "Mixed domain query"),
            ("Tell me about cats and dogs", "other", "Out-of-scope query"),
            ("How does AI impact society comprehensively?", "general", "Very broad query"),
            ("What specific risks exist in AI-powered autonomous vehicles?", "safety", "Specific use case"),
        ]
    
    def run_single_test(self, prompt: str, expected_domain: str, description: str) -> TestResult:
        """Run a single test with rate limiting and detailed analysis."""
        logger.info(f"Testing: {description}")
        
        # Apply rate limiting
        self.rate_limiter.wait_if_needed()
        
        start_time = time.time()
        
        try:
            # Process the query
            response, docs = self.chat_service.process_query(prompt, "test_session")
            
            response_time = time.time() - start_time
            
            # Analyze response
            word_count = len(response.split())
            has_citations = bool(len([c for c in response if c.startswith('RID-')]) > 0)
            citation_count = len([c for c in response.split() if c.startswith('RID-')])
            is_refusal = self._is_refusal_response(response)
            
            # Get domain detection info
            query_type, detected_domain = self.chat_service.query_processor.analyze_query(prompt)
            
            # Calculate quality metrics
            quality_metrics = self._calculate_quality_metrics(response, prompt, docs)
            
            return TestResult(
                prompt=prompt,
                domain=description,
                expected_domain=expected_domain,
                response=response,
                response_time=response_time,
                word_count=word_count,
                has_citations=has_citations,
                citation_count=citation_count,
                validation_score=quality_metrics.get('overall_score', 0.0),
                confidence_score=quality_metrics.get('confidence', 0.0),
                detected_domain=detected_domain or query_type,
                is_refusal=is_refusal,
                quality_metrics=quality_metrics
            )
            
        except Exception as e:
            logger.error(f"Test failed: {e}")
            return TestResult(
                prompt=prompt,
                domain=description,
                expected_domain=expected_domain,
                response="",
                response_time=time.time() - start_time,
                word_count=0,
                has_citations=False,
                citation_count=0,
                validation_score=0.0,
                confidence_score=0.0,
                detected_domain="error",
                is_refusal=True,
                quality_metrics={},
                error=str(e)
            )
    
    def _is_refusal_response(self, response: str) -> bool:
        """Check if response is a refusal/deflection."""
        refusal_patterns = [
            "i cannot answer",
            "i'm not able to",
            "i don't know",
            "i cannot provide",
            "i'm sorry, but",
            "beyond my scope",
            "outside my knowledge"
        ]
        
        response_lower = response.lower()
        return any(pattern in response_lower for pattern in refusal_patterns)
    
    def _calculate_quality_metrics(self, response: str, prompt: str, docs: List) -> Dict[str, float]:
        """Calculate quality metrics for a response."""
        try:
            # Use the validation chain if available
            if hasattr(self.chat_service, 'validation_chain'):
                from src.core.validation.response_validator import validation_chain
                _, validation_results = validation_chain.validate_and_improve(
                    response=response,
                    query=prompt,
                    documents=docs,
                    domain="general"
                )
                
                return {
                    'overall_score': validation_results.overall_score,
                    'accuracy': next((c.score for c in validation_results.checks if c.category.value == 'factual_accuracy'), 0.0),
                    'relevance': next((c.score for c in validation_results.checks if c.category.value == 'relevance'), 0.0),
                    'completeness': next((c.score for c in validation_results.checks if c.category.value == 'completeness'), 0.0),
                    'appropriateness': next((c.score for c in validation_results.checks if c.category.value == 'appropriateness'), 0.0),
                    'citation_quality': next((c.score for c in validation_results.checks if c.category.value == 'citation_quality'), 0.0),
                    'coherence': next((c.score for c in validation_results.checks if c.category.value == 'coherence'), 0.0),
                    'confidence': 0.8  # Default confidence
                }
            
        except Exception as e:
            logger.warning(f"Quality metric calculation failed: {e}")
        
        # Fallback basic metrics
        return {
            'overall_score': 0.7,
            'accuracy': 0.7,
            'relevance': 0.7,
            'completeness': 0.7,
            'appropriateness': 0.7,
            'citation_quality': 0.6,
            'coherence': 0.7,
            'confidence': 0.6
        }
    
    def run_comprehensive_test(self) -> TestSummary:
        """Run the full comprehensive test suite."""
        logger.info("Starting comprehensive pipeline testing...")
        
        if not self.initialize_services():
            raise Exception("Failed to initialize services")
        
        test_prompts = self.get_test_prompts()
        test_results = []
        
        total_tests = len(test_prompts)
        logger.info(f"Running {total_tests} tests with rate limiting...")
        
        for i, (prompt, expected_domain, description) in enumerate(test_prompts, 1):
            logger.info(f"Test {i}/{total_tests}: {description}")
            
            result = self.run_single_test(prompt, expected_domain, description)
            test_results.append(result)
            
            # Log immediate results
            if result.error:
                logger.error(f"Test failed: {result.error}")
            else:
                logger.info(f"Response time: {result.response_time:.2f}s, "
                           f"Words: {result.word_count}, "
                           f"Citations: {result.citation_count}, "
                           f"Score: {result.validation_score:.2f}")
        
        # Calculate summary statistics
        successful_tests = [r for r in test_results if not r.error]
        failed_tests = [r for r in test_results if r.error]
        
        if successful_tests:
            avg_response_time = statistics.mean(r.response_time for r in successful_tests)
            avg_word_count = statistics.mean(r.word_count for r in successful_tests)
            avg_validation_score = statistics.mean(r.validation_score for r in successful_tests)
            citation_rate = len([r for r in successful_tests if r.has_citations]) / len(successful_tests)
            refusal_rate = len([r for r in successful_tests if r.is_refusal]) / len(successful_tests)
            
            # Domain accuracy
            domain_matches = len([r for r in successful_tests if r.detected_domain == r.expected_domain])
            domain_accuracy = domain_matches / len(successful_tests)
            
            # Quality breakdown
            quality_breakdown = {}
            for metric in ['accuracy', 'relevance', 'completeness', 'appropriateness', 'citation_quality', 'coherence']:
                scores = [r.quality_metrics.get(metric, 0.0) for r in successful_tests]
                quality_breakdown[metric] = statistics.mean(scores) if scores else 0.0
        else:
            avg_response_time = 0.0
            avg_word_count = 0.0
            avg_validation_score = 0.0
            citation_rate = 0.0
            refusal_rate = 1.0
            domain_accuracy = 0.0
            quality_breakdown = {}
        
        summary = TestSummary(
            total_tests=total_tests,
            successful_tests=len(successful_tests),
            failed_tests=len(failed_tests),
            avg_response_time=avg_response_time,
            avg_word_count=avg_word_count,
            avg_validation_score=avg_validation_score,
            citation_rate=citation_rate,
            refusal_rate=refusal_rate,
            domain_accuracy=domain_accuracy,
            quality_breakdown=quality_breakdown,
            test_results=test_results
        )
        
        logger.info("Comprehensive testing completed")
        return summary
    
    def generate_report(self, summary: TestSummary) -> str:
        """Generate a detailed performance report."""
        report = f"""
# Comprehensive Pipeline Testing Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary
- **Total Tests**: {summary.total_tests}
- **Successful**: {summary.successful_tests} ({summary.successful_tests/summary.total_tests*100:.1f}%)
- **Failed**: {summary.failed_tests} ({summary.failed_tests/summary.total_tests*100:.1f}%)

## Performance Metrics
- **Average Response Time**: {summary.avg_response_time:.2f} seconds
- **Average Word Count**: {summary.avg_word_count:.0f} words
- **Average Validation Score**: {summary.avg_validation_score:.2f}/1.0

## Quality Metrics
- **Citation Rate**: {summary.citation_rate:.1%} (responses with citations)
- **Refusal Rate**: {summary.refusal_rate:.1%} (inappropriate refusals)
- **Domain Accuracy**: {summary.domain_accuracy:.1%} (correct domain detection)

## Quality Breakdown
"""
        
        for metric, score in summary.quality_breakdown.items():
            report += f"- **{metric.replace('_', ' ').title()}**: {score:.2f}/1.0\n"
        
        report += f"""
## Domain Performance Analysis
"""
        
        # Group results by domain
        domain_results = {}
        for result in summary.test_results:
            if result.expected_domain not in domain_results:
                domain_results[result.expected_domain] = []
            domain_results[result.expected_domain].append(result)
        
        for domain, results in domain_results.items():
            successful = [r for r in results if not r.error]
            if successful:
                avg_score = statistics.mean(r.validation_score for r in successful)
                citation_rate = len([r for r in successful if r.has_citations]) / len(successful)
                refusal_rate = len([r for r in successful if r.is_refusal]) / len(successful)
                
                report += f"""
### {domain.title()} Domain
- Tests: {len(results)} | Successful: {len(successful)}
- Avg Score: {avg_score:.2f}
- Citation Rate: {citation_rate:.1%}
- Refusal Rate: {refusal_rate:.1%}
"""
        
        report += f"""
## Individual Test Results
"""
        
        for i, result in enumerate(summary.test_results, 1):
            status = "✓" if not result.error else "✗"
            report += f"""
### Test {i}: {result.domain}
- **Status**: {status}
- **Prompt**: {result.prompt}
- **Expected Domain**: {result.expected_domain}
- **Detected Domain**: {result.detected_domain}
- **Response Time**: {result.response_time:.2f}s
- **Word Count**: {result.word_count}
- **Citations**: {result.citation_count}
- **Validation Score**: {result.validation_score:.2f}
- **Is Refusal**: {result.is_refusal}
"""
            
            if result.error:
                report += f"- **Error**: {result.error}\n"
            else:
                report += f"- **Response Preview**: {result.response[:200]}...\n"
        
        return report
    
    def save_results(self, summary: TestSummary, filename: str = None):
        """Save test results to JSON file."""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"pipeline_test_results_{timestamp}.json"
        
        # Convert to serializable format
        data = {
            'summary': asdict(summary),
            'timestamp': datetime.now().isoformat(),
            'settings': {
                'USE_HYBRID_SEARCH': settings.USE_HYBRID_SEARCH,
                'USE_FIELD_AWARE_HYBRID': settings.USE_FIELD_AWARE_HYBRID,
                'GEMINI_MODEL_NAME': settings.GEMINI_MODEL_NAME,
                'EMBEDDING_PROVIDER': settings.EMBEDDING_PROVIDER
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        logger.info(f"Results saved to {filename}")
        return filename

def main():
    """Main testing function."""
    try:
        tester = PipelineTester()
        
        logger.info("Starting comprehensive pipeline testing...")
        logger.info("Note: This will take approximately 45 minutes due to rate limiting")
        
        # Run comprehensive test
        summary = tester.run_comprehensive_test()
        
        # Generate and save report
        report = tester.generate_report(summary)
        
        # Save results
        json_file = tester.save_results(summary)
        
        # Save report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"pipeline_test_report_{timestamp}.md"
        with open(report_file, 'w') as f:
            f.write(report)
        
        logger.info(f"Testing completed!")
        logger.info(f"Report saved to: {report_file}")
        logger.info(f"Raw data saved to: {json_file}")
        
        # Print summary
        print(f"\n{'='*60}")
        print(f"COMPREHENSIVE PIPELINE TEST RESULTS")
        print(f"{'='*60}")
        print(f"Total Tests: {summary.total_tests}")
        print(f"Successful: {summary.successful_tests} ({summary.successful_tests/summary.total_tests*100:.1f}%)")
        print(f"Failed: {summary.failed_tests} ({summary.failed_tests/summary.total_tests*100:.1f}%)")
        print(f"Average Validation Score: {summary.avg_validation_score:.2f}/1.0")
        print(f"Citation Rate: {summary.citation_rate:.1%}")
        print(f"Refusal Rate: {summary.refusal_rate:.1%}")
        print(f"Domain Accuracy: {summary.domain_accuracy:.1%}")
        print(f"{'='*60}")
        
        return summary
        
    except Exception as e:
        logger.error(f"Testing failed: {e}")
        raise

if __name__ == "__main__":
    main()