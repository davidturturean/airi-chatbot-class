"""
Handler for taxonomy-specific queries about the AI Risk Repository.
Provides structured, complete responses for taxonomy questions based on the preprint.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from ...config.logging import get_logger

logger = get_logger(__name__)

@dataclass
class TaxonomyResponse:
    """Structured response for taxonomy queries."""
    content: str
    taxonomy_type: str  # 'causal', 'domain', or 'both'
    source: str = "AI Risk Repository Preprint (Slattery et al., 2024)"
    confidence: float = 1.0


class TaxonomyHandler:
    """Handles taxonomy-specific queries with structured data from the preprint."""
    
    def __init__(self):
        """Initialize taxonomy data structures from the preprint."""
        self._init_causal_taxonomy()
        self._init_domain_taxonomy()
    
    def _init_causal_taxonomy(self):
        """Initialize the Causal Taxonomy structure."""
        self.causal_taxonomy = {
            "name": "Causal Taxonomy of AI Risks",
            "description": "Classifies AI risks by their causal factors",
            "categories": {
                "Entity": {
                    "description": "The entity that causes the risk through a decision or action",
                    "options": ["Human", "AI", "Other"],
                    "details": {
                        "Human": "Risk caused by human decision or action",
                        "AI": "Risk caused by AI system decision or action",
                        "Other": "Risk without clearly specified causal entity"
                    }
                },
                "Intentionality": {
                    "description": "Whether the risk was an expected or unexpected outcome",
                    "options": ["Intentional", "Unintentional", "Other"],
                    "details": {
                        "Intentional": "Risk as expected outcome of pursuing a goal",
                        "Unintentional": "Risk as unexpected outcome",
                        "Other": "Risk without clearly specified intentionality"
                    }
                },
                "Timing": {
                    "description": "The stage in the AI lifecycle when the risk occurs",
                    "options": ["Pre-deployment", "Post-deployment", "Other"],
                    "details": {
                        "Pre-deployment": "Risk occurs before the AI model is deployed",
                        "Post-deployment": "Risk occurs after the AI model has been trained and deployed",
                        "Other": "Risk without clearly specified timing"
                    }
                }
            },
            "statistics": {
                "entity": {"Human": "39%", "AI": "41%", "Other": "20%"},
                "intentionality": {"Intentional": "34%", "Unintentional": "35%", "Other": "31%"},
                "timing": {"Pre-deployment": "13%", "Post-deployment": "62%", "Other": "25%"}
            }
        }
    
    def _init_domain_taxonomy(self):
        """Initialize the Domain Taxonomy structure with 7 domains and 24 subdomains."""
        self.domain_taxonomy = {
            "name": "Domain Taxonomy of AI Risks",
            "description": "Classifies AI risks into 7 domains and 24 subdomains",
            "domains": [
                {
                    "id": 1,
                    "name": "Discrimination & Toxicity",
                    "description": "Risks related to AI systems producing discriminatory outputs or exposing users to toxic content",
                    "subdomains": [
                        "Discrimination & bias",
                        "Exposure to toxic content",
                        "Aggression & violence"
                    ],
                    "percentage": "16.2%"
                },
                {
                    "id": 2,
                    "name": "Privacy & Security",
                    "description": "Risks involving data privacy violations, security vulnerabilities, and unauthorized access",
                    "subdomains": [
                        "Privacy violations",
                        "Security vulnerabilities & attacks",
                        "Data leaks & unauthorized access"
                    ],
                    "percentage": "15.8%"
                },
                {
                    "id": 3,
                    "name": "Misinformation",
                    "description": "Risks from AI generating or spreading false, misleading, or harmful information",
                    "subdomains": [
                        "Generating or spreading misinformation",
                        "Harmful content generation",
                        "Information manipulation"
                    ],
                    "percentage": "12.4%"
                },
                {
                    "id": 4,
                    "name": "Malicious Actors & Misuse",
                    "description": "Risks from intentional misuse of AI systems for harmful purposes",
                    "subdomains": [
                        "Fraud & deception",
                        "Malicious use",
                        "Competitive & geopolitical risks"
                    ],
                    "percentage": "11.6%"
                },
                {
                    "id": 5,
                    "name": "Human-Computer Interaction",
                    "description": "Risks arising from how humans interact with and are affected by AI systems",
                    "subdomains": [
                        "Overreliance on AI",
                        "Manipulation & anthropomorphism",
                        "Automation & employment",
                        "Degradation of human capabilities"
                    ],
                    "percentage": "14.9%"
                },
                {
                    "id": 6,
                    "name": "Socioeconomic & Environmental",
                    "description": "Broader societal, economic, and environmental impacts of AI systems",
                    "subdomains": [
                        "Concentration of power",
                        "Environmental impacts",
                        "Societal & cultural harms",
                        "Economic harms"
                    ],
                    "percentage": "13.5%"
                },
                {
                    "id": 7,
                    "name": "AI System Safety, Failures, & Limitations",
                    "description": "Technical risks related to AI system performance, reliability, and safety",
                    "subdomains": [
                        "Performance issues",
                        "Safety & alignment problems",
                        "Lack of transparency & explainability",
                        "Weaponization & mass destruction",
                        "Existential risks",
                        "Other system risks"
                    ],
                    "percentage": "15.6%"
                }
            ],
            "total_subdomains": 24,
            "total_risks": 1612,
            "documents_analyzed": 65
        }
    
    def handle_taxonomy_query(self, query: str) -> TaxonomyResponse:
        """Handle a taxonomy-specific query and return structured response."""
        query_lower = query.lower()
        
        # Determine which taxonomy is being asked about
        if any(term in query_lower for term in ['causal', 'entity', 'intentionality', 'timing', 'pre-deployment', 'post-deployment']):
            return self._get_causal_taxonomy_response(query_lower)
        elif any(term in query_lower for term in ['domain', '7 domain', '24 subdomain', 'discrimination', 'privacy', 'misinformation']):
            return self._get_domain_taxonomy_response(query_lower)
        elif 'risk categories' in query_lower or 'main categories' in query_lower or 'ai risk database v3' in query_lower:
            return self._get_both_taxonomies_response(query_lower)
        else:
            # Default to showing both taxonomies
            return self._get_both_taxonomies_response(query_lower)
    
    def _get_causal_taxonomy_response(self, query: str) -> TaxonomyResponse:
        """Generate response for causal taxonomy queries."""
        content = f"""## Causal Taxonomy of AI Risks

The AI Risk Repository uses a **Causal Taxonomy** that classifies risks based on three key dimensions:

### 1. **Entity** (Who/what causes the risk?)
- **Human** ({self.causal_taxonomy['statistics']['entity']['Human']} of risks): Risks caused by human decisions or actions
- **AI** ({self.causal_taxonomy['statistics']['entity']['AI']} of risks): Risks caused by AI system decisions or actions  
- **Other** ({self.causal_taxonomy['statistics']['entity']['Other']} of risks): Risks without clearly specified causal entity

### 2. **Intentionality** (Was it intended?)
- **Intentional** ({self.causal_taxonomy['statistics']['intentionality']['Intentional']} of risks): Risk as expected outcome of pursuing a goal
- **Unintentional** ({self.causal_taxonomy['statistics']['intentionality']['Unintentional']} of risks): Risk as unexpected outcome
- **Other** ({self.causal_taxonomy['statistics']['intentionality']['Other']} of risks): Risk without clearly specified intentionality

### 3. **Timing** (When does it occur?)
- **Pre-deployment** ({self.causal_taxonomy['statistics']['timing']['Pre-deployment']} of risks): Risk occurs before the AI model is deployed
- **Post-deployment** ({self.causal_taxonomy['statistics']['timing']['Post-deployment']} of risks): Risk occurs after the AI model has been trained and deployed
- **Other** ({self.causal_taxonomy['statistics']['timing']['Other']} of risks): Risk without clearly specified timing

This taxonomy allows systematic classification of any AI risk by identifying the causal entity, whether the harm was intentional, and when in the AI lifecycle it occurs.

*Source: The AI Risk Repository (Slattery et al., 2024)*"""
        
        return TaxonomyResponse(
            content=content,
            taxonomy_type="causal",
            source=self.causal_taxonomy.get('source', 'AI Risk Repository Preprint')
        )
    
    def _get_domain_taxonomy_response(self, query: str) -> TaxonomyResponse:
        """Generate response for domain taxonomy queries."""
        
        # Build the domain list
        domain_list = []
        for domain in self.domain_taxonomy['domains']:
            subdomains_str = "\n   - ".join(domain['subdomains'])
            domain_list.append(f"""
### {domain['id']}. **{domain['name']}** ({domain['percentage']} of risks)
{domain['description']}

**Subdomains:**
   - {subdomains_str}""")
        
        content = f"""## Domain Taxonomy of AI Risks

The AI Risk Repository organizes risks into **7 domains** and **24 subdomains** based on analysis of {self.domain_taxonomy['total_risks']} risks from {self.domain_taxonomy['documents_analyzed']} documents:

{"".join(domain_list)}

### Summary Statistics:
- **Total Domains:** 7
- **Total Subdomains:** 24  
- **Total Risks Analyzed:** {self.domain_taxonomy['total_risks']}
- **Documents Reviewed:** {self.domain_taxonomy['documents_analyzed']}

This comprehensive taxonomy provides a structured framework for understanding and categorizing the full spectrum of AI risks.

*Source: The AI Risk Repository (Slattery et al., 2024)*"""
        
        return TaxonomyResponse(
            content=content,
            taxonomy_type="domain",
            source="AI Risk Repository Preprint"
        )
    
    def _get_both_taxonomies_response(self, query: str) -> TaxonomyResponse:
        """Generate response showing both taxonomies."""
        
        # Simplified domain list for overview
        domain_names = [f"{d['id']}. {d['name']}" for d in self.domain_taxonomy['domains']]
        
        content = f"""## AI Risk Repository Taxonomy Structure

The AI Risk Repository uses two complementary taxonomies to classify AI risks:

### 1. **Causal Taxonomy** - How risks emerge
Classifies risks by three causal factors:
- **Entity**: Human, AI, or Other
- **Intentionality**: Intentional, Unintentional, or Other  
- **Timing**: Pre-deployment, Post-deployment, or Other

### 2. **Domain Taxonomy** - Types of risks
Organizes risks into 7 domains and 24 subdomains:

{chr(10).join(domain_names)}

Each domain is further divided into specific subdomains, totaling 24 subcategories.

### Key Statistics:
- **Total Risks Catalogued:** {self.domain_taxonomy['total_risks']}
- **Documents Analyzed:** {self.domain_taxonomy['documents_analyzed']}
- **Most Common Timing:** Post-deployment (62% of risks)
- **Most Common Entity:** AI-caused (41% of risks)

These taxonomies work together to provide comprehensive classification - the Causal Taxonomy explains *how and when* risks occur, while the Domain Taxonomy categorizes *what types* of risks exist.

*Source: The AI Risk Repository (Slattery et al., 2024)*"""
        
        return TaxonomyResponse(
            content=content,
            taxonomy_type="both",
            source="AI Risk Repository Preprint"
        )
    
    def get_specific_domain(self, domain_id: int) -> Optional[Dict[str, Any]]:
        """Get details for a specific domain by ID."""
        for domain in self.domain_taxonomy['domains']:
            if domain['id'] == domain_id:
                return domain
        return None
    
    def get_all_subdomains(self) -> List[str]:
        """Get a flat list of all 24 subdomains."""
        subdomains = []
        for domain in self.domain_taxonomy['domains']:
            subdomains.extend(domain['subdomains'])
        return subdomains