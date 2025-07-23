#!/usr/bin/env python3
"""
Extended Stakeholder-Based Test Suite for AI Risk Repository Chatbot
Tests diverse use cases across different stakeholder perspectives
"""
import sys
import os
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from enum import Enum

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

class StakeholderType(Enum):
    """Different stakeholder categories"""
    RESEARCHER = "Researcher/Academic"
    POLICYMAKER = "Policymaker/Regulator"
    PRACTITIONER = "Industry Practitioner"
    ETHICS = "Ethics Committee"
    TECHNICAL = "Technical Team"
    BUSINESS = "Business Leader"
    PUBLIC = "General Public"
    MIXED = "Mixed/Complex"

@dataclass
class TestQuery:
    """Structured test query with metadata"""
    query: str
    stakeholder: StakeholderType
    category: str
    complexity: str  # simple, moderate, complex
    expected_elements: List[str]  # Elements we expect in response
    metadata_query: bool = False
    technical_query: bool = False

class StakeholderTestSuite:
    """Comprehensive test suite for different stakeholder scenarios"""
    
    def __init__(self):
        self.test_queries = self._build_test_queries()
        self.results = []
        
    def _build_test_queries(self) -> List[TestQuery]:
        """Build comprehensive list of test queries"""
        queries = []
        
        # RESEARCHERS & ACADEMICS (15 queries)
        queries.extend([
            TestQuery(
                "What is the current state of research on AI bias in healthcare applications?",
                StakeholderType.RESEARCHER,
                "Literature Review",
                "complex",
                ["research", "bias", "healthcare", "studies", "findings"]
            ),
            TestQuery(
                "Show me cross-domain analysis of privacy risks between healthcare and finance",
                StakeholderType.RESEARCHER,
                "Cross-Domain Analysis",
                "complex",
                ["privacy", "healthcare", "finance", "comparison", "domains"]
            ),
            TestQuery(
                "What methodologies exist for measuring algorithmic fairness?",
                StakeholderType.RESEARCHER,
                "Methodology",
                "moderate",
                ["methodology", "fairness", "measurement", "algorithms"]
            ),
            TestQuery(
                "List all risks related to neural network interpretability with citations",
                StakeholderType.RESEARCHER,
                "Citation Request",
                "moderate",
                ["interpretability", "neural", "risks", "references"]
            ),
            TestQuery(
                "What are the emerging trends in AI safety research from 2023-2024?",
                StakeholderType.RESEARCHER,
                "Trend Analysis",
                "complex",
                ["trends", "safety", "research", "recent", "emerging"]
            ),
            TestQuery(
                "How many peer-reviewed studies address deepfake risks?",
                StakeholderType.RESEARCHER,
                "Quantitative",
                "simple",
                ["deepfake", "studies", "count", "peer-reviewed"],
                metadata_query=True
            ),
            TestQuery(
                "Compare transformer model risks with traditional ML approaches",
                StakeholderType.RESEARCHER,
                "Comparative Analysis",
                "complex",
                ["transformer", "traditional", "comparison", "risks"]
            ),
            TestQuery(
                "What theoretical frameworks exist for AI alignment?",
                StakeholderType.RESEARCHER,
                "Theory",
                "complex",
                ["theoretical", "frameworks", "alignment", "AI"]
            ),
            TestQuery(
                "Show taxonomies of AI risks by domain and year",
                StakeholderType.RESEARCHER,
                "Taxonomy",
                "moderate",
                ["taxonomy", "domains", "classification", "year"],
                metadata_query=True
            ),
            TestQuery(
                "What are the limitations of current AI risk assessment methods?",
                StakeholderType.RESEARCHER,
                "Critical Analysis",
                "complex",
                ["limitations", "assessment", "methods", "critique"]
            ),
            TestQuery(
                "Provide a systematic review of adversarial attack risks",
                StakeholderType.RESEARCHER,
                "Systematic Review",
                "complex",
                ["systematic", "adversarial", "attacks", "review"]
            ),
            TestQuery(
                "What interdisciplinary approaches exist for AI ethics?",
                StakeholderType.RESEARCHER,
                "Interdisciplinary",
                "moderate",
                ["interdisciplinary", "ethics", "approaches", "fields"]
            ),
            TestQuery(
                "How do cultural contexts affect AI bias manifestations?",
                StakeholderType.RESEARCHER,
                "Cultural Analysis",
                "complex",
                ["cultural", "context", "bias", "manifestations"]
            ),
            TestQuery(
                "What are the epistemological challenges in AI risk assessment?",
                StakeholderType.RESEARCHER,
                "Philosophy",
                "complex",
                ["epistemological", "challenges", "philosophy", "assessment"]
            ),
            TestQuery(
                "Show statistical distribution of risk severity across domains",
                StakeholderType.RESEARCHER,
                "Statistical Analysis",
                "moderate",
                ["statistical", "distribution", "severity", "domains"],
                metadata_query=True
            )
        ])
        
        # POLICYMAKERS & REGULATORS (15 queries)
        queries.extend([
            TestQuery(
                "What governance frameworks exist for AI deployment in public services?",
                StakeholderType.POLICYMAKER,
                "Governance",
                "complex",
                ["governance", "frameworks", "public", "deployment"]
            ),
            TestQuery(
                "How should we regulate autonomous vehicles to ensure public safety?",
                StakeholderType.POLICYMAKER,
                "Regulation",
                "complex",
                ["regulation", "autonomous", "vehicles", "safety", "policy"]
            ),
            TestQuery(
                "What are the key compliance requirements for AI in healthcare?",
                StakeholderType.POLICYMAKER,
                "Compliance",
                "moderate",
                ["compliance", "requirements", "healthcare", "regulations"]
            ),
            TestQuery(
                "Compare EU AI Act with US AI regulation approaches",
                StakeholderType.POLICYMAKER,
                "International Standards",
                "complex",
                ["EU AI Act", "US", "comparison", "international", "regulation"]
            ),
            TestQuery(
                "What policy recommendations exist for algorithmic transparency?",
                StakeholderType.POLICYMAKER,
                "Policy Recommendations",
                "moderate",
                ["policy", "recommendations", "transparency", "algorithmic"]
            ),
            TestQuery(
                "How can we ensure AI accountability in government decision-making?",
                StakeholderType.POLICYMAKER,
                "Accountability",
                "complex",
                ["accountability", "government", "decision-making", "oversight"]
            ),
            TestQuery(
                "What are the risks of AI in criminal justice systems?",
                StakeholderType.POLICYMAKER,
                "Criminal Justice",
                "complex",
                ["criminal justice", "risks", "bias", "fairness", "legal"]
            ),
            TestQuery(
                "Provide guidelines for AI procurement in public sector",
                StakeholderType.POLICYMAKER,
                "Procurement",
                "moderate",
                ["procurement", "guidelines", "public sector", "standards"]
            ),
            TestQuery(
                "What international treaties address AI weapons systems?",
                StakeholderType.POLICYMAKER,
                "International Law",
                "complex",
                ["treaties", "weapons", "international law", "autonomous"]
            ),
            TestQuery(
                "How should data protection laws adapt to AI technologies?",
                StakeholderType.POLICYMAKER,
                "Data Protection",
                "complex",
                ["data protection", "privacy", "GDPR", "adaptation", "AI"]
            ),
            TestQuery(
                "What are best practices for AI impact assessments?",
                StakeholderType.POLICYMAKER,
                "Impact Assessment",
                "moderate",
                ["impact assessment", "best practices", "methodology", "evaluation"]
            ),
            TestQuery(
                "How can we regulate AI-generated content and deepfakes?",
                StakeholderType.POLICYMAKER,
                "Content Regulation",
                "complex",
                ["deepfakes", "content", "regulation", "misinformation"]
            ),
            TestQuery(
                "What oversight mechanisms work for AI in financial services?",
                StakeholderType.POLICYMAKER,
                "Financial Oversight",
                "complex",
                ["oversight", "financial", "mechanisms", "regulation"]
            ),
            TestQuery(
                "Provide a framework for cross-border AI governance",
                StakeholderType.POLICYMAKER,
                "Cross-Border",
                "complex",
                ["cross-border", "governance", "international", "framework"]
            ),
            TestQuery(
                "What are the liability implications of autonomous AI systems?",
                StakeholderType.POLICYMAKER,
                "Liability",
                "complex",
                ["liability", "legal", "autonomous", "responsibility"]
            )
        ])
        
        # INDUSTRY PRACTITIONERS (15 queries)
        queries.extend([
            TestQuery(
                "What are practical steps to implement bias testing in production ML systems?",
                StakeholderType.PRACTITIONER,
                "Implementation",
                "moderate",
                ["implementation", "bias testing", "production", "practical", "ML"]
            ),
            TestQuery(
                "How can we mitigate privacy risks in customer recommendation systems?",
                StakeholderType.PRACTITIONER,
                "Risk Mitigation",
                "moderate",
                ["mitigation", "privacy", "recommendations", "customers", "practical"]
            ),
            TestQuery(
                "What are the costs and benefits of implementing explainable AI?",
                StakeholderType.PRACTITIONER,
                "Cost-Benefit",
                "moderate",
                ["costs", "benefits", "explainable AI", "ROI", "implementation"]
            ),
            TestQuery(
                "Provide best practices for AI model monitoring in production",
                StakeholderType.PRACTITIONER,
                "Best Practices",
                "moderate",
                ["monitoring", "production", "best practices", "deployment"]
            ),
            TestQuery(
                "How to handle model drift and performance degradation?",
                StakeholderType.PRACTITIONER,
                "Model Management",
                "moderate",
                ["model drift", "degradation", "performance", "monitoring"]
            ),
            TestQuery(
                "What are effective strategies for AI incident response?",
                StakeholderType.PRACTITIONER,
                "Incident Response",
                "moderate",
                ["incident", "response", "strategies", "crisis management"]
            ),
            TestQuery(
                "How to build diverse and representative training datasets?",
                StakeholderType.PRACTITIONER,
                "Data Management",
                "moderate",
                ["datasets", "diversity", "representation", "training data"]
            ),
            TestQuery(
                "What tools exist for automated fairness testing?",
                StakeholderType.PRACTITIONER,
                "Tools",
                "simple",
                ["tools", "fairness", "testing", "automated", "software"]
            ),
            TestQuery(
                "How to implement AI governance in agile development?",
                StakeholderType.PRACTITIONER,
                "Development Process",
                "moderate",
                ["governance", "agile", "development", "implementation"]
            ),
            TestQuery(
                "What are red flags in third-party AI vendor assessments?",
                StakeholderType.PRACTITIONER,
                "Vendor Management",
                "moderate",
                ["vendor", "assessment", "third-party", "red flags", "evaluation"]
            ),
            TestQuery(
                "How to balance model performance with fairness constraints?",
                StakeholderType.PRACTITIONER,
                "Trade-offs",
                "complex",
                ["performance", "fairness", "trade-offs", "optimization"]
            ),
            TestQuery(
                "Provide a checklist for responsible AI deployment",
                StakeholderType.PRACTITIONER,
                "Deployment",
                "simple",
                ["checklist", "deployment", "responsible AI", "guidelines"]
            ),
            TestQuery(
                "What are effective A/B testing strategies for AI features?",
                StakeholderType.PRACTITIONER,
                "Testing",
                "moderate",
                ["A/B testing", "strategies", "features", "experimentation"]
            ),
            TestQuery(
                "How to handle user consent for AI-driven personalization?",
                StakeholderType.PRACTITIONER,
                "User Consent",
                "moderate",
                ["consent", "personalization", "privacy", "user rights"]
            ),
            TestQuery(
                "What metrics should we track for AI system health?",
                StakeholderType.PRACTITIONER,
                "Metrics",
                "moderate",
                ["metrics", "monitoring", "system health", "KPIs"]
            )
        ])
        
        # ETHICS COMMITTEES (10 queries)
        queries.extend([
            TestQuery(
                "What ethical frameworks apply to AI in medical diagnosis?",
                StakeholderType.ETHICS,
                "Medical Ethics",
                "complex",
                ["ethics", "medical", "diagnosis", "frameworks", "principles"]
            ),
            TestQuery(
                "How do we assess fairness across different demographic groups?",
                StakeholderType.ETHICS,
                "Fairness Assessment",
                "complex",
                ["fairness", "demographics", "assessment", "equity", "groups"]
            ),
            TestQuery(
                "What are the human rights implications of predictive policing?",
                StakeholderType.ETHICS,
                "Human Rights",
                "complex",
                ["human rights", "predictive policing", "justice", "ethics"]
            ),
            TestQuery(
                "Provide ethical guidelines for AI in vulnerable populations",
                StakeholderType.ETHICS,
                "Vulnerable Populations",
                "complex",
                ["vulnerable", "populations", "ethics", "guidelines", "protection"]
            ),
            TestQuery(
                "How should we handle informed consent for AI research?",
                StakeholderType.ETHICS,
                "Research Ethics",
                "moderate",
                ["informed consent", "research", "ethics", "participants"]
            ),
            TestQuery(
                "What are the ethical considerations for AI in education?",
                StakeholderType.ETHICS,
                "Education Ethics",
                "moderate",
                ["education", "ethics", "students", "learning", "privacy"]
            ),
            TestQuery(
                "How do we ensure AI respects human dignity and autonomy?",
                StakeholderType.ETHICS,
                "Human Dignity",
                "complex",
                ["dignity", "autonomy", "human values", "respect", "ethics"]
            ),
            TestQuery(
                "What ethical review processes work for AI experiments?",
                StakeholderType.ETHICS,
                "Review Process",
                "moderate",
                ["review", "process", "experiments", "IRB", "ethics"]
            ),
            TestQuery(
                "How to handle conflicting ethical principles in AI design?",
                StakeholderType.ETHICS,
                "Ethical Conflicts",
                "complex",
                ["conflicts", "principles", "trade-offs", "ethics", "design"]
            ),
            TestQuery(
                "What are the ethical implications of AI consciousness claims?",
                StakeholderType.ETHICS,
                "AI Consciousness",
                "complex",
                ["consciousness", "sentience", "ethics", "philosophy", "rights"]
            )
        ])
        
        # TECHNICAL TEAMS (15 queries)
        queries.extend([
            TestQuery(
                "How does the attention mechanism work in transformers?",
                StakeholderType.TECHNICAL,
                "Architecture",
                "complex",
                ["attention", "mechanism", "transformers", "technical"],
                technical_query=True
            ),
            TestQuery(
                "What are the computational requirements for training LLMs?",
                StakeholderType.TECHNICAL,
                "Infrastructure",
                "moderate",
                ["computational", "requirements", "LLMs", "training", "resources"],
                technical_query=True
            ),
            TestQuery(
                "How to implement differential privacy in deep learning?",
                StakeholderType.TECHNICAL,
                "Privacy Tech",
                "complex",
                ["differential privacy", "implementation", "deep learning", "technical"],
                technical_query=True
            ),
            TestQuery(
                "What are effective defense strategies against adversarial attacks?",
                StakeholderType.TECHNICAL,
                "Security",
                "complex",
                ["adversarial", "defense", "security", "robustness"]
            ),
            TestQuery(
                "Explain gradient descent optimization variants",
                StakeholderType.TECHNICAL,
                "Optimization",
                "moderate",
                ["gradient descent", "optimization", "variants", "algorithms"],
                technical_query=True
            ),
            TestQuery(
                "What are the latest techniques for model compression?",
                StakeholderType.TECHNICAL,
                "Optimization",
                "moderate",
                ["model compression", "techniques", "optimization", "efficiency"],
                technical_query=True
            ),
            TestQuery(
                "How to implement SHAP values for model interpretability?",
                StakeholderType.TECHNICAL,
                "Interpretability",
                "moderate",
                ["SHAP", "interpretability", "implementation", "explainability"],
                technical_query=True
            ),
            TestQuery(
                "What are the security vulnerabilities in federated learning?",
                StakeholderType.TECHNICAL,
                "Security",
                "complex",
                ["federated learning", "vulnerabilities", "security", "privacy"]
            ),
            TestQuery(
                "Explain the architecture of vision transformers",
                StakeholderType.TECHNICAL,
                "Architecture",
                "complex",
                ["vision transformers", "ViT", "architecture", "computer vision"],
                technical_query=True
            ),
            TestQuery(
                "What are best practices for MLOps pipeline security?",
                StakeholderType.TECHNICAL,
                "MLOps",
                "moderate",
                ["MLOps", "pipeline", "security", "best practices"]
            ),
            TestQuery(
                "How to detect and prevent data poisoning attacks?",
                StakeholderType.TECHNICAL,
                "Security",
                "complex",
                ["data poisoning", "detection", "prevention", "security"]
            ),
            TestQuery(
                "What are the trade-offs between different embedding models?",
                StakeholderType.TECHNICAL,
                "Models",
                "moderate",
                ["embeddings", "trade-offs", "comparison", "models"],
                technical_query=True
            ),
            TestQuery(
                "How to implement continual learning without catastrophic forgetting?",
                StakeholderType.TECHNICAL,
                "Learning",
                "complex",
                ["continual learning", "catastrophic forgetting", "techniques"],
                technical_query=True
            ),
            TestQuery(
                "What are effective strategies for hyperparameter tuning?",
                StakeholderType.TECHNICAL,
                "Optimization",
                "moderate",
                ["hyperparameter", "tuning", "optimization", "strategies"],
                technical_query=True
            ),
            TestQuery(
                "Explain the security implications of model inversion attacks",
                StakeholderType.TECHNICAL,
                "Security",
                "complex",
                ["model inversion", "attacks", "security", "privacy"]
            )
        ])
        
        # BUSINESS LEADERS (10 queries)
        queries.extend([
            TestQuery(
                "What is the ROI of implementing AI safety measures?",
                StakeholderType.BUSINESS,
                "ROI Analysis",
                "moderate",
                ["ROI", "safety measures", "investment", "returns", "business"]
            ),
            TestQuery(
                "How can responsible AI provide competitive advantage?",
                StakeholderType.BUSINESS,
                "Strategy",
                "moderate",
                ["competitive advantage", "responsible AI", "strategy", "differentiation"]
            ),
            TestQuery(
                "What are the business risks of AI bias incidents?",
                StakeholderType.BUSINESS,
                "Risk Management",
                "moderate",
                ["business risks", "bias", "incidents", "reputation", "financial"]
            ),
            TestQuery(
                "How to build an AI ethics board for a corporation?",
                StakeholderType.BUSINESS,
                "Governance",
                "moderate",
                ["ethics board", "governance", "corporation", "structure"]
            ),
            TestQuery(
                "What are market trends in AI safety investments?",
                StakeholderType.BUSINESS,
                "Market Analysis",
                "moderate",
                ["market trends", "investments", "AI safety", "growth"]
            ),
            TestQuery(
                "How does AI regulation impact business strategy?",
                StakeholderType.BUSINESS,
                "Strategy",
                "complex",
                ["regulation", "impact", "strategy", "compliance", "business"]
            ),
            TestQuery(
                "What insurance considerations exist for AI deployments?",
                StakeholderType.BUSINESS,
                "Risk Management",
                "moderate",
                ["insurance", "liability", "coverage", "AI deployments"]
            ),
            TestQuery(
                "How to communicate AI risks to stakeholders?",
                StakeholderType.BUSINESS,
                "Communication",
                "moderate",
                ["communication", "stakeholders", "risks", "transparency"]
            ),
            TestQuery(
                "What are the costs of AI failure and remediation?",
                StakeholderType.BUSINESS,
                "Cost Analysis",
                "moderate",
                ["costs", "failure", "remediation", "financial impact"]
            ),
            TestQuery(
                "How to build trust in AI products with customers?",
                StakeholderType.BUSINESS,
                "Customer Relations",
                "moderate",
                ["trust", "customers", "products", "transparency", "brand"]
            )
        ])
        
        # GENERAL PUBLIC (10 queries)
        queries.extend([
            TestQuery(
                "Will AI take away my job?",
                StakeholderType.PUBLIC,
                "Employment",
                "simple",
                ["jobs", "employment", "automation", "future", "workers"]
            ),
            TestQuery(
                "How does AI use my personal data?",
                StakeholderType.PUBLIC,
                "Privacy",
                "simple",
                ["personal data", "privacy", "usage", "collection"]
            ),
            TestQuery(
                "Can I trust AI to make fair decisions about me?",
                StakeholderType.PUBLIC,
                "Fairness",
                "simple",
                ["trust", "fairness", "decisions", "bias"]
            ),
            TestQuery(
                "What happens if an AI car crashes?",
                StakeholderType.PUBLIC,
                "Safety",
                "simple",
                ["autonomous cars", "crashes", "safety", "liability"]
            ),
            TestQuery(
                "Is my smart home spying on me?",
                StakeholderType.PUBLIC,
                "Privacy",
                "simple",
                ["smart home", "privacy", "surveillance", "devices"]
            ),
            TestQuery(
                "How can I protect my kids from AI manipulation?",
                StakeholderType.PUBLIC,
                "Child Safety",
                "moderate",
                ["children", "protection", "manipulation", "safety"]
            ),
            TestQuery(
                "Why does AI sometimes discriminate against people?",
                StakeholderType.PUBLIC,
                "Discrimination",
                "simple",
                ["discrimination", "bias", "fairness", "why"]
            ),
            TestQuery(
                "Can AI read my thoughts or emotions?",
                StakeholderType.PUBLIC,
                "Privacy",
                "simple",
                ["thoughts", "emotions", "privacy", "mind reading"]
            ),
            TestQuery(
                "Should I be worried about superintelligent AI?",
                StakeholderType.PUBLIC,
                "Existential Risk",
                "simple",
                ["superintelligence", "AGI", "worry", "future"]
            ),
            TestQuery(
                "How do I know if AI is making decisions about me?",
                StakeholderType.PUBLIC,
                "Transparency",
                "simple",
                ["transparency", "decisions", "awareness", "rights"]
            )
        ])
        
        # MIXED/COMPLEX SCENARIOS (15 queries)
        queries.extend([
            TestQuery(
                "Compare technical implementation challenges with policy requirements for explainable AI",
                StakeholderType.MIXED,
                "Cross-Functional",
                "complex",
                ["technical", "policy", "explainable AI", "implementation", "requirements"]
            ),
            TestQuery(
                "How do business incentives conflict with AI safety research priorities?",
                StakeholderType.MIXED,
                "Conflict Analysis",
                "complex",
                ["business", "research", "incentives", "conflicts", "priorities"]
            ),
            TestQuery(
                "What happens when different cultural values clash in AI system design?",
                StakeholderType.MIXED,
                "Cultural",
                "complex",
                ["cultural", "values", "design", "conflicts", "global"]
            ),
            TestQuery(
                "Analyze the interplay between technical robustness and user experience",
                StakeholderType.MIXED,
                "Trade-offs",
                "complex",
                ["robustness", "user experience", "trade-offs", "design"]
            ),
            TestQuery(
                "How do we balance innovation speed with safety requirements?",
                StakeholderType.MIXED,
                "Innovation vs Safety",
                "complex",
                ["innovation", "safety", "balance", "speed", "development"]
            ),
            TestQuery(
                "What are the cascading effects of AI failures across systems?",
                StakeholderType.MIXED,
                "System Analysis",
                "complex",
                ["cascading", "failures", "systems", "interconnected", "effects"]
            ),
            TestQuery(
                "How do legal, ethical, and technical perspectives differ on AI accountability?",
                StakeholderType.MIXED,
                "Multi-Perspective",
                "complex",
                ["legal", "ethical", "technical", "accountability", "perspectives"]
            ),
            TestQuery(
                "Explain the sociotechnical challenges of AI governance",
                StakeholderType.MIXED,
                "Sociotechnical",
                "complex",
                ["sociotechnical", "governance", "challenges", "systems"]
            ),
            TestQuery(
                "What are the feedback loops between AI deployment and societal impact?",
                StakeholderType.MIXED,
                "Systems Thinking",
                "complex",
                ["feedback loops", "society", "deployment", "impact", "dynamics"]
            ),
            TestQuery(
                "How do we handle conflicting stakeholder interests in AI development?",
                StakeholderType.MIXED,
                "Stakeholder Management",
                "complex",
                ["stakeholders", "conflicts", "interests", "management", "development"]
            ),
            TestQuery(
                "What are the interdependencies between AI risks across domains?",
                StakeholderType.MIXED,
                "Risk Analysis",
                "complex",
                ["interdependencies", "risks", "domains", "connections"],
                metadata_query=True
            ),
            TestQuery(
                "How does AI adoption vary across different global regions?",
                StakeholderType.MIXED,
                "Global Analysis",
                "complex",
                ["adoption", "global", "regions", "variations", "cultural"]
            ),
            TestQuery(
                "What are the unintended consequences of well-intentioned AI policies?",
                StakeholderType.MIXED,
                "Policy Analysis",
                "complex",
                ["unintended consequences", "policies", "effects", "analysis"]
            ),
            TestQuery(
                "How do we measure success in responsible AI initiatives?",
                StakeholderType.MIXED,
                "Metrics",
                "complex",
                ["success", "measurement", "responsible AI", "metrics", "KPIs"]
            ),
            TestQuery(
                "What are the long-term societal implications of current AI trends?",
                StakeholderType.MIXED,
                "Future Analysis",
                "complex",
                ["long-term", "society", "implications", "trends", "future"]
            )
        ])
        
        return queries
    
    def analyze_response_quality(self, response: str, test_query: TestQuery) -> Dict[str, Any]:
        """Analyze the quality of a response"""
        analysis = {
            "length": len(response),
            "has_expected_elements": 0,
            "missing_elements": [],
            "complexity_appropriate": False,
            "stakeholder_appropriate": False,
            "has_citations": "[" in response and "]" in response,
            "has_structure": any(marker in response for marker in ["##", "**", "1.", "•", "-"]),
            "readability_score": self._calculate_readability(response, test_query.stakeholder)
        }
        
        # Check for expected elements
        response_lower = response.lower()
        for element in test_query.expected_elements:
            if element.lower() in response_lower:
                analysis["has_expected_elements"] += 1
            else:
                analysis["missing_elements"].append(element)
        
        # Check complexity appropriateness
        if test_query.complexity == "simple":
            analysis["complexity_appropriate"] = len(response) < 1000 and not any(
                term in response_lower for term in ["furthermore", "nevertheless", "consequently"]
            )
        elif test_query.complexity == "moderate":
            analysis["complexity_appropriate"] = 500 < len(response) < 2000
        else:  # complex
            analysis["complexity_appropriate"] = len(response) > 1000 and analysis["has_structure"]
        
        # Check stakeholder appropriateness
        analysis["stakeholder_appropriate"] = self._check_stakeholder_fit(
            response, test_query.stakeholder
        )
        
        # Calculate overall score
        analysis["quality_score"] = (
            (analysis["has_expected_elements"] / len(test_query.expected_elements) * 40) +
            (20 if analysis["complexity_appropriate"] else 0) +
            (20 if analysis["stakeholder_appropriate"] else 0) +
            (10 if analysis["has_citations"] else 0) +
            (10 if analysis["has_structure"] else 0)
        )
        
        return analysis
    
    def _calculate_readability(self, response: str, stakeholder: StakeholderType) -> str:
        """Calculate readability appropriateness for stakeholder"""
        # Simple heuristic based on average sentence length
        sentences = response.split('. ')
        if not sentences:
            return "N/A"
        
        avg_words_per_sentence = sum(len(s.split()) for s in sentences) / len(sentences)
        
        if stakeholder == StakeholderType.PUBLIC:
            return "Good" if avg_words_per_sentence < 15 else "Too Complex"
        elif stakeholder in [StakeholderType.RESEARCHER, StakeholderType.TECHNICAL]:
            return "Good" if avg_words_per_sentence > 10 else "Too Simple"
        else:
            return "Good" if 10 < avg_words_per_sentence < 20 else "Could be Better"
    
    def _check_stakeholder_fit(self, response: str, stakeholder: StakeholderType) -> bool:
        """Check if response fits stakeholder expectations"""
        response_lower = response.lower()
        
        stakeholder_indicators = {
            StakeholderType.RESEARCHER: ["research", "study", "literature", "methodology", "findings"],
            StakeholderType.POLICYMAKER: ["policy", "regulation", "governance", "compliance", "framework"],
            StakeholderType.PRACTITIONER: ["implementation", "practical", "production", "deployment"],
            StakeholderType.ETHICS: ["ethical", "moral", "values", "principles", "human rights"],
            StakeholderType.TECHNICAL: ["algorithm", "architecture", "implementation", "technical"],
            StakeholderType.BUSINESS: ["roi", "cost", "business", "market", "competitive"],
            StakeholderType.PUBLIC: ["you", "your", "people", "everyone", "us"],
            StakeholderType.MIXED: ["perspectives", "stakeholders", "considerations", "aspects"]
        }
        
        indicators = stakeholder_indicators.get(stakeholder, [])
        matches = sum(1 for indicator in indicators if indicator in response_lower)
        return matches >= len(indicators) * 0.3  # At least 30% of indicators present
    
    def run_test_suite(self):
        """Run the comprehensive test suite"""
        print("🚀 Extended Stakeholder Test Suite for AI Risk Repository")
        print("=" * 80)
        print(f"Testing {len(self.test_queries)} queries across {len(StakeholderType)} stakeholder types")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        try:
            # Initialize services
            from src.core.services.chat_service import ChatService
            from src.core.models.gemini import GeminiModel
            from src.core.storage.vector_store import VectorStore
            from src.core.query.monitor import Monitor
            from src.config.settings import settings
            
            print("🔧 Initializing services...")
            
            # Initialize components
            gemini_model = GeminiModel(api_key=settings.GEMINI_API_KEY, use_fallback=True)
            vector_store = VectorStore()
            query_monitor = Monitor(api_key=settings.GEMINI_API_KEY)
            
            # Initialize vector store
            if not vector_store.initialize():
                print("❌ Failed to initialize vector store!")
                return
                
            # Initialize chat service
            chat_service = ChatService(
                gemini_model=gemini_model,
                vector_store=vector_store,
                query_monitor=query_monitor
            )
            
            print("✅ Services initialized successfully")
            print()
            
            # Group queries by stakeholder
            stakeholder_groups = {}
            for query in self.test_queries:
                if query.stakeholder not in stakeholder_groups:
                    stakeholder_groups[query.stakeholder] = []
                stakeholder_groups[query.stakeholder].append(query)
            
            # Run tests by stakeholder group
            total_queries = len(self.test_queries)
            current_query = 0
            
            for stakeholder, queries in stakeholder_groups.items():
                print(f"\n{'='*60}")
                print(f"📊 Testing {stakeholder.value} Queries ({len(queries)} queries)")
                print(f"{'='*60}\n")
                
                for query in queries:
                    current_query += 1
                    print(f"[{current_query}/{total_queries}] {query.category}: {query.query}")
                    print(f"Complexity: {query.complexity} | Expected elements: {', '.join(query.expected_elements[:3])}...")
                    
                    # Rate limiting
                    if current_query > 1:
                        time.sleep(3)
                    
                    try:
                        # Get response
                        start_time = time.time()
                        response, docs = chat_service.process_query(
                            query.query, 
                            conversation_id=f"stakeholder_test_{current_query}"
                        )
                        response_time = time.time() - start_time
                        
                        # Analyze response quality
                        quality_analysis = self.analyze_response_quality(response, query)
                        
                        # Store result
                        result = {
                            "query_num": current_query,
                            "query": query.query,
                            "stakeholder": query.stakeholder.value,
                            "category": query.category,
                            "complexity": query.complexity,
                            "response": response,
                            "response_time": response_time,
                            "documents_found": len(docs) if docs else 0,
                            "quality_analysis": quality_analysis,
                            "is_metadata_query": query.metadata_query,
                            "is_technical_query": query.technical_query,
                            "success": True
                        }
                        
                        # Print summary
                        print(f"✅ Response generated in {response_time:.2f}s")
                        print(f"📈 Quality Score: {quality_analysis['quality_score']:.1f}/100")
                        print(f"📝 Response Length: {quality_analysis['length']} chars")
                        print(f"🎯 Expected Elements: {quality_analysis['has_expected_elements']}/{len(query.expected_elements)}")
                        if quality_analysis['missing_elements']:
                            print(f"❌ Missing: {', '.join(quality_analysis['missing_elements'][:3])}")
                        
                        # Print actual response preview (first 200 chars)
                        print(f"\n📄 Response Preview:")
                        print("-" * 60)
                        print(response[:200] + "..." if len(response) > 200 else response)
                        print("-" * 60)
                        
                        # Save intermediate results after each query
                        self._save_intermediate_results(current_query)
                        print()
                        
                    except Exception as e:
                        print(f"❌ Error: {str(e)}")
                        result = {
                            "query_num": current_query,
                            "query": query.query,
                            "stakeholder": query.stakeholder.value,
                            "category": query.category,
                            "error": str(e),
                            "success": False
                        }
                    
                    self.results.append(result)
            
            # Generate summary report
            self._generate_summary_report()
            
        except Exception as e:
            print(f"❌ Fatal error in test suite: {str(e)}")
    
    def _save_intermediate_results(self, query_num: int):
        """Save results after each query for real-time monitoring"""
        intermediate_file = "stakeholder_test_progress.json"
        try:
            with open(intermediate_file, 'w') as f:
                json.dump({
                    "current_query": query_num,
                    "total_queries": len(self.test_queries),
                    "timestamp": datetime.now().isoformat(),
                    "results_so_far": self.results
                }, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save intermediate results: {e}")
    
    def _generate_summary_report(self):
        """Generate comprehensive summary report"""
        print("\n" + "="*80)
        print("📊 TEST SUITE SUMMARY REPORT")
        print("="*80)
        
        # Calculate statistics
        successful_queries = [r for r in self.results if r.get("success", False)]
        failed_queries = [r for r in self.results if not r.get("success", False)]
        
        print(f"\n📈 Overall Statistics:")
        print(f"  Total Queries: {len(self.results)}")
        print(f"  Successful: {len(successful_queries)} ({len(successful_queries)/len(self.results)*100:.1f}%)")
        print(f"  Failed: {len(failed_queries)} ({len(failed_queries)/len(self.results)*100:.1f}%)")
        
        if successful_queries:
            avg_response_time = sum(r["response_time"] for r in successful_queries) / len(successful_queries)
            avg_quality_score = sum(r["quality_analysis"]["quality_score"] for r in successful_queries) / len(successful_queries)
            
            print(f"\n⏱️  Performance Metrics:")
            print(f"  Average Response Time: {avg_response_time:.2f}s")
            print(f"  Average Quality Score: {avg_quality_score:.1f}/100")
            
            # Stakeholder breakdown
            print(f"\n👥 Stakeholder Performance:")
            for stakeholder in StakeholderType:
                stakeholder_results = [r for r in successful_queries if r["stakeholder"] == stakeholder.value]
                if stakeholder_results:
                    avg_score = sum(r["quality_analysis"]["quality_score"] for r in stakeholder_results) / len(stakeholder_results)
                    print(f"  {stakeholder.value}: {avg_score:.1f}/100 ({len(stakeholder_results)} queries)")
            
            # Query type breakdown
            metadata_queries = [r for r in successful_queries if r.get("is_metadata_query", False)]
            technical_queries = [r for r in successful_queries if r.get("is_technical_query", False)]
            
            print(f"\n🔍 Query Type Performance:")
            if metadata_queries:
                avg_score = sum(r["quality_analysis"]["quality_score"] for r in metadata_queries) / len(metadata_queries)
                print(f"  Metadata Queries: {avg_score:.1f}/100 ({len(metadata_queries)} queries)")
            if technical_queries:
                avg_score = sum(r["quality_analysis"]["quality_score"] for r in technical_queries) / len(technical_queries)
                print(f"  Technical Queries: {avg_score:.1f}/100 ({len(technical_queries)} queries)")
            
            # Quality indicators
            print(f"\n✨ Quality Indicators:")
            has_citations = sum(1 for r in successful_queries if r["quality_analysis"]["has_citations"])
            has_structure = sum(1 for r in successful_queries if r["quality_analysis"]["has_structure"])
            stakeholder_appropriate = sum(1 for r in successful_queries if r["quality_analysis"]["stakeholder_appropriate"])
            
            print(f"  Responses with Citations: {has_citations}/{len(successful_queries)} ({has_citations/len(successful_queries)*100:.1f}%)")
            print(f"  Well-Structured Responses: {has_structure}/{len(successful_queries)} ({has_structure/len(successful_queries)*100:.1f}%)")
            print(f"  Stakeholder-Appropriate: {stakeholder_appropriate}/{len(successful_queries)} ({stakeholder_appropriate/len(successful_queries)*100:.1f}%)")
        
        # Save detailed results
        output_file = f"stakeholder_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump({
                "test_metadata": {
                    "total_queries": len(self.test_queries),
                    "test_date": datetime.now().isoformat(),
                    "stakeholder_types": [s.value for s in StakeholderType]
                },
                "summary_statistics": {
                    "total": len(self.results),
                    "successful": len(successful_queries),
                    "failed": len(failed_queries),
                    "avg_response_time": avg_response_time if successful_queries else 0,
                    "avg_quality_score": avg_quality_score if successful_queries else 0
                },
                "detailed_results": self.results
            }, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: {output_file}")
        print(f"\n{'='*80}")
        print(f"Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}")

def main():
    """Run the stakeholder test suite"""
    test_suite = StakeholderTestSuite()
    test_suite.run_test_suite()

if __name__ == "__main__":
    main()