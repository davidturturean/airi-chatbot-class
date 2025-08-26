"""
Handler for taxonomy-specific queries about the AI Risk Repository.
Provides structured, complete responses for taxonomy questions based on the preprint.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from ...config.logging import get_logger
from ..query.query_intent_analyzer import QueryIntentAnalyzer, QueryIntent

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
        self.intent_analyzer = QueryIntentAnalyzer()
    
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
                        "Unfair discrimination and misrepresentation",
                        "Exposure to toxic content",
                        "Unequal performance across groups"
                    ],
                    "percentage": "15%"
                },
                {
                    "id": 2,
                    "name": "Privacy & Security",
                    "description": "Risks involving data privacy violations, security vulnerabilities, and unauthorized access",
                    "subdomains": [
                        "Compromise of privacy by obtaining, leaking, or correctly inferring sensitive information",
                        "AI system security vulnerabilities and attacks"
                    ],
                    "percentage": "12%"
                },
                {
                    "id": 3,
                    "name": "Misinformation",
                    "description": "Risks from AI generating or spreading false, misleading, or harmful information",
                    "subdomains": [
                        "False or misleading information",
                        "Pollution of information ecosystem and loss of consensus reality"
                    ],
                    "percentage": "4%"
                },
                {
                    "id": 4,
                    "name": "Malicious Actors & Misuse",
                    "description": "Risks from intentional misuse of AI systems for harmful purposes",
                    "subdomains": [
                        "Disinformation, surveillance, and influence at scale",
                        "Cyberattacks, weapon development or use, and mass harm",
                        "Fraud, scams, and targeted manipulation"
                    ],
                    "percentage": "16%"
                },
                {
                    "id": 5,
                    "name": "Human-Computer Interaction",
                    "description": "Risks arising from how humans interact with and are affected by AI systems",
                    "subdomains": [
                        "Overreliance and unsafe use",
                        "Loss of human agency and autonomy"
                    ],
                    "percentage": "7%"
                },
                {
                    "id": 6,
                    "name": "Socioeconomic & Environmental",
                    "description": "Broader societal, economic, and environmental impacts of AI systems",
                    "subdomains": [
                        "Power centralization and unfair distribution of benefits",
                        "Increased inequality and decline in employment quality",
                        "Economic and cultural devaluation of human effort",
                        "Competitive dynamics",
                        "Governance failure",
                        "Environmental harm"
                    ],
                    "percentage": "19%"
                },
                {
                    "id": 7,
                    "name": "AI System Safety, Failures, & Limitations",
                    "description": "Technical risks related to AI system performance, reliability, and safety",
                    "subdomains": [
                        "AI pursuing its own goals in conflict with human goals or values",
                        "AI possessing dangerous capabilities",
                        "Lack of capability or robustness",
                        "Lack of transparency or interpretability",
                        "AI welfare and rights",
                        "Multi-agent risks"
                    ],
                    "percentage": "26%"
                }
            ],
            "total_subdomains": 24,
            "total_risks": 1612,
            "documents_analyzed": 65
        }
    
    def handle_taxonomy_query(self, query: str) -> TaxonomyResponse:
        """Handle a taxonomy-specific query and return structured response."""
        query_lower = query.lower()
        
        # Analyze query intent semantically
        intent = self.intent_analyzer.analyze_query(query)
        
        # Analyze query focus for routing
        query_focus = self._analyze_query_focus(query_lower)
        
        # Route based on both intent and focus analysis
        if query_focus['is_search']:
            return self._get_search_context_response(query_lower)
        elif query_focus['is_specific_domain']:
            return self._get_specific_domain_response(query_lower, query_focus['domain_id'])
        elif intent.comparison_mode and self._is_intentionality_comparison(query_lower):
            return self._get_intentionality_comparison_response(intent)
        elif intent.enumeration_mode and 'subdomain' in query_lower:
            return self._get_all_subdomains_response(intent)
        elif query_focus['is_timing_focused']:
            return self._get_timing_focused_response(query_lower)
        elif query_focus['is_statistical']:
            return self._get_statistical_response(query_lower)
        elif query_focus['is_causal']:
            return self._get_adaptive_causal_response(query_lower, intent)
        elif query_focus['is_domain_list']:
            return self._get_adaptive_domain_response(query_lower, intent)
        else:
            # Intelligent routing based on concepts mentioned
            if 'intentional' in intent.concepts_mentioned or 'unintentional' in intent.concepts_mentioned:
                if intent.comparison_mode:
                    return self._get_intentionality_comparison_response(intent)
                else:
                    return self._get_adaptive_causal_response(query_lower, intent)
            elif any(term in query_lower for term in ['organize', 'structure', 'framework', 'categorize', 'classify']):
                return self._get_adaptive_both_response(query_lower, intent)
            elif any(term in query_lower for term in ['entity', 'timing', 'when', 'who']):
                return self._get_adaptive_causal_response(query_lower, intent)
            elif any(term in query_lower for term in ['domain', 'type', 'kind', 'category']):
                return self._get_adaptive_domain_response(query_lower, intent)
            else:
                return self._get_adaptive_both_response(query_lower, intent)
    
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
    
    def _analyze_query_focus(self, query: str) -> Dict[str, Any]:
        """Analyze what aspect of the taxonomy the query is asking about."""
        focus = {
            'is_search': False,
            'is_specific_domain': False,
            'domain_id': None,
            'is_timing_focused': False,
            'is_statistical': False,
            'is_causal': False,
            'is_domain_list': False
        }
        
        # Check for search queries
        if any(term in query for term in ['find', 'search', 'papers', 'documents', 'studies']):
            focus['is_search'] = True
        
        # Check for specific domain references
        domain_keywords = {
            1: ['discrimination', 'toxicity', 'bias', 'toxic'],
            2: ['privacy', 'security', 'data protection', 'vulnerabilities'],
            3: ['misinformation', 'fake', 'false information', 'misleading'],
            4: ['malicious', 'misuse', 'fraud', 'deception'],
            5: ['human-computer', 'hci', 'interaction', 'automation', 'employment'],
            6: ['socioeconomic', 'environmental', 'societal', 'economic'],
            7: ['safety', 'failures', 'limitations', 'alignment', 'existential']
        }
        
        for domain_id, keywords in domain_keywords.items():
            if any(kw in query for kw in keywords):
                focus['is_specific_domain'] = True
                focus['domain_id'] = domain_id
                break
        
        # Check for domain number references
        import re
        domain_match = re.search(r'domain\s*(\d)', query)
        if domain_match:
            focus['is_specific_domain'] = True
            focus['domain_id'] = int(domain_match.group(1))
        
        # Check for timing focus
        if any(term in query for term in ['timing', 'pre-deployment', 'post-deployment', 'before deployment', 'after deployment', 'when']):
            focus['is_timing_focused'] = True
        
        # Check for statistical queries
        if any(term in query for term in ['percentage', 'percent', 'how many', 'proportion', 'statistics', 'number of']):
            focus['is_statistical'] = True
        
        # Check for causal taxonomy indicators
        if any(term in query for term in ['entity', 'intentionality', 'causal', 'who causes', 'human vs ai']):
            focus['is_causal'] = True
        
        # Check for domain list queries
        if any(term in query for term in ['7 domains', 'seven domains', 'all domains', 'list domains', 'what domains']):
            focus['is_domain_list'] = True
        
        return focus
    
    def _get_search_context_response(self, query: str) -> TaxonomyResponse:
        """Provide taxonomy context for search queries."""
        # Extract what they're searching for
        if 'pre-deployment' in query or 'before deployment' in query:
            content = f"""## Pre-deployment Risks in the AI Risk Repository

**Pre-deployment** is a key timing category in our Causal Taxonomy, representing {self.causal_taxonomy['statistics']['timing']['Pre-deployment']} of all documented risks.

### Understanding Pre-deployment Risks:
These are risks that occur **before** an AI model is deployed to production, including:
- Design flaws and biases introduced during development
- Training data issues and poisoning
- Inadequate testing and validation
- Misalignment with intended goals

### Context in the Causal Taxonomy:
Pre-deployment risks can be:
- **Human-caused**: Poor design decisions, biased data collection
- **AI-caused**: Model behavior during training/testing
- **Intentional or Unintentional**: Deliberate choices vs oversights

### Related Domains:
Pre-deployment risks appear across all 7 domains but are particularly relevant for:
- **Discrimination & Toxicity**: Biased training data
- **AI System Safety**: Alignment and testing issues
- **Privacy & Security**: Data handling during development

*To search for specific pre-deployment papers, the system will now search the document repository...*

*Source: The AI Risk Repository (Slattery et al., 2024)*"""
        else:
            # Generic search context
            content = self._get_both_taxonomies_response(query).content
        
        return TaxonomyResponse(
            content=content,
            taxonomy_type="search_context",
            source="AI Risk Repository Preprint"
        )
    
    def _get_specific_domain_response(self, query: str, domain_id: int) -> TaxonomyResponse:
        """Provide detailed information about a specific domain."""
        domain = self.get_specific_domain(domain_id)
        if not domain:
            return self._get_domain_taxonomy_response(query)
        
        subdomains_str = "\n   - ".join(domain['subdomains'])
        
        content = f"""## Domain {domain['id']}: {domain['name']}

{domain['description']}

### Key Statistics:
- **Percentage of all risks**: {domain['percentage']}
- **Number of subdomains**: {len(domain['subdomains'])}

### Subdomains:
   - {subdomains_str}

### Context in Repository:
This is one of 7 domains in the AI Risk Repository's Domain Taxonomy, which organizes {self.domain_taxonomy['total_risks']} risks from {self.domain_taxonomy['documents_analyzed']} documents.

### Related Domains:
"""
        
        # Add related domains based on common patterns
        if domain_id == 2:  # Privacy & Security
            content += "- **Misinformation** (Domain 3): Privacy breaches can enable misinformation\n"
            content += "- **Malicious Actors** (Domain 4): Security vulnerabilities exploited maliciously\n"
        elif domain_id == 1:  # Discrimination
            content += "- **Human-Computer Interaction** (Domain 5): Biased AI affects user interactions\n"
            content += "- **Socioeconomic** (Domain 6): Discrimination has societal impacts\n"
        
        content += f"\n*Source: The AI Risk Repository (Slattery et al., 2024)*"
        
        return TaxonomyResponse(
            content=content,
            taxonomy_type="specific_domain",
            source="AI Risk Repository Preprint"
        )
    
    def _get_timing_focused_response(self, query: str) -> TaxonomyResponse:
        """Provide timing-focused causal taxonomy information."""
        content = f"""## Timing in the AI Risk Causal Taxonomy

The **Timing** dimension is one of three key factors in the Causal Taxonomy, categorizing when risks occur in the AI lifecycle.

### Timing Categories:

#### 1. **Pre-deployment** ({self.causal_taxonomy['statistics']['timing']['Pre-deployment']} of risks)
- **Definition**: Risks occurring before the AI model is deployed to production
- **Examples**: 
  - Biased training data collection
  - Flawed model architecture decisions
  - Inadequate testing procedures
  - Misalignment during training

#### 2. **Post-deployment** ({self.causal_taxonomy['statistics']['timing']['Post-deployment']} of risks)
- **Definition**: Risks occurring after the AI model has been trained and deployed
- **Examples**:
  - Misuse by end users
  - Emergent behaviors in production
  - Adversarial attacks
  - Drift from original training distribution

#### 3. **Other** ({self.causal_taxonomy['statistics']['timing']['Other']} of risks)
- **Definition**: Risks without clearly specified timing
- **Examples**: Systemic or ongoing risks that span the lifecycle

### Interaction with Other Causal Factors:
- **Entity**: Both humans and AI can cause risks at either timing stage
- **Intentionality**: Pre-deployment often involves unintentional oversights; post-deployment sees more intentional misuse

### Key Insight:
The majority of risks ({self.causal_taxonomy['statistics']['timing']['Post-deployment']}) occur **post-deployment**, highlighting the importance of ongoing monitoring and governance.

*Source: The AI Risk Repository (Slattery et al., 2024)*"""
        
        return TaxonomyResponse(
            content=content,
            taxonomy_type="timing_focused",
            source="AI Risk Repository Preprint"
        )
    
    def _get_statistical_response(self, query: str) -> TaxonomyResponse:
        """Provide statistical information about the taxonomies."""
        content = f"""## AI Risk Repository Statistics

### Overall Repository:
- **Total Risks Documented**: {self.domain_taxonomy['total_risks']}
- **Documents Analyzed**: {self.domain_taxonomy['documents_analyzed']}
- **Domains**: 7
- **Subdomains**: 24

### Causal Taxonomy Distribution:

#### By Entity (Who causes the risk?):
- **AI-caused**: {self.causal_taxonomy['statistics']['entity']['AI']}
- **Human-caused**: {self.causal_taxonomy['statistics']['entity']['Human']}
- **Other/Unspecified**: {self.causal_taxonomy['statistics']['entity']['Other']}

#### By Intentionality:
- **Intentional**: {self.causal_taxonomy['statistics']['intentionality']['Intentional']}
- **Unintentional**: {self.causal_taxonomy['statistics']['intentionality']['Unintentional']}
- **Other/Unspecified**: {self.causal_taxonomy['statistics']['intentionality']['Other']}

#### By Timing:
- **Pre-deployment**: {self.causal_taxonomy['statistics']['timing']['Pre-deployment']}
- **Post-deployment**: {self.causal_taxonomy['statistics']['timing']['Post-deployment']}
- **Other/Unspecified**: {self.causal_taxonomy['statistics']['timing']['Other']}

### Domain Taxonomy Distribution:
"""
        
        for domain in self.domain_taxonomy['domains']:
            content += f"\n{domain['id']}. **{domain['name']}**: {domain['percentage']} of risks"
        
        content += """\n\n### Key Findings:
- Post-deployment risks are most common (62%)
- AI and humans cause roughly equal proportions of risks
- AI System Safety, Failures, & Limitations is the largest domain (26%)

*Source: The AI Risk Repository (Slattery et al., 2024)*"""
        
        return TaxonomyResponse(
            content=content,
            taxonomy_type="statistical",
            source="AI Risk Repository Preprint"
        )
    
    def _is_intentionality_comparison(self, query: str) -> bool:
        """Check if query is comparing intentional vs unintentional."""
        return ('intentional' in query and 'unintentional' in query) or \
               ('difference' in query and 'intentional' in query)
    
    def _get_intentionality_comparison_response(self, intent: QueryIntent) -> TaxonomyResponse:
        """Provide comparison between intentional and unintentional risks."""
        content = f"""## Intentional vs Unintentional Risks

### Understanding the Intentionality Dimension

The **Intentionality** dimension in the Causal Taxonomy distinguishes between risks based on whether harmful outcomes were expected or unexpected.

### Key Differences:

#### **Intentional Risks** ({self.causal_taxonomy['statistics']['intentionality']['Intentional']} of all risks)
- **Definition**: Risk as an **expected outcome** of pursuing a goal
- **Characteristics**:
  - Actor knows harmful outcome is likely or certain
  - Harm is accepted as cost of achieving objective
  - Often involves trade-offs or calculated decisions
- **Examples**:
  - Using AI for surveillance despite privacy concerns
  - Deploying biased systems for economic advantage
  - Weaponizing AI capabilities
  - Accepting job displacement as cost of automation

#### **Unintentional Risks** ({self.causal_taxonomy['statistics']['intentionality']['Unintentional']} of all risks)
- **Definition**: Risk as an **unexpected outcome**
- **Characteristics**:
  - Harm was not anticipated or desired
  - Often results from oversight, error, or emergence
  - May involve unforeseen consequences
- **Examples**:
  - Bias from incomplete training data
  - Unexpected model behaviors in production
  - System failures from edge cases
  - Unintended discrimination from proxy variables

### Distribution Analysis:
- Nearly **equal split**: Intentional (34%) vs Unintentional (35%)
- Remaining 31% are risks without clearly specified intentionality
- This balance suggests AI risks arise equally from deliberate choices and unexpected consequences

### Interaction with Other Dimensions:
- **Timing**: Intentional risks more common post-deployment (misuse)
- **Entity**: Both humans and AI can cause intentional/unintentional risks
- **Domains**: Malicious use typically intentional; discrimination often unintentional

*Source: The AI Risk Repository (Slattery et al., 2024)*"""
        
        return TaxonomyResponse(
            content=content,
            taxonomy_type="comparison",
            source="AI Risk Repository Preprint"
        )
    
    def _get_all_subdomains_response(self, intent: QueryIntent) -> TaxonomyResponse:
        """Provide complete listing of all 24 subdomains."""
        content = """## Complete List of 24 AI Risk Subdomains

The AI Risk Repository organizes risks into **7 domains** containing **24 total subdomains**:

"""
        
        for domain in self.domain_taxonomy['domains']:
            content += f"### Domain {domain['id']}: {domain['name']} ({domain['percentage']})\n"
            content += f"{domain['description']}\n\n"
            content += "**Subdomains:**\n"
            for i, subdomain in enumerate(domain['subdomains'], 1):
                content += f"{i}. {subdomain}\n"
            content += "\n"
        
        content += f"""### Summary:
- **Total Subdomains:** 24
- **Domains:** 7
- **Risks Analyzed:** {self.domain_taxonomy['total_risks']}
- **Documents:** {self.domain_taxonomy['documents_analyzed']}

This complete enumeration covers all risk categories identified in the repository's comprehensive analysis.

*Source: The AI Risk Repository (Slattery et al., 2024)*"""
        
        return TaxonomyResponse(
            content=content,
            taxonomy_type="enumeration",
            source="AI Risk Repository Preprint"
        )
    
    def _get_adaptive_causal_response(self, query: str, intent: QueryIntent) -> TaxonomyResponse:
        """Generate adaptive causal taxonomy response based on intent."""
        detail_level = self.intent_analyzer.get_response_detail_level(intent)
        
        if detail_level == 'exhaustive' or intent.completeness_level >= 0.7:
            # Provide complete causal taxonomy with all details
            return self._get_causal_taxonomy_response(query)
        else:
            # Provide standard or summary based on completeness
            return self._get_causal_taxonomy_response(query)
    
    def _get_adaptive_domain_response(self, query: str, intent: QueryIntent) -> TaxonomyResponse:
        """Generate adaptive domain taxonomy response based on intent."""
        detail_level = self.intent_analyzer.get_response_detail_level(intent)
        
        # Check if asking for complete subdomain list
        if intent.enumeration_mode and ('subdomain' in query or '24' in query):
            return self._get_all_subdomains_response(intent)
        elif detail_level == 'exhaustive' or intent.completeness_level >= 0.7:
            # Provide complete domain taxonomy with all subdomains
            return self._get_domain_taxonomy_response(query)
        else:
            # Provide overview
            return self._get_both_taxonomies_response(query)
    
    def _get_adaptive_both_response(self, query: str, intent: QueryIntent) -> TaxonomyResponse:
        """Generate adaptive response showing both taxonomies based on intent."""
        detail_level = self.intent_analyzer.get_response_detail_level(intent)
        
        if detail_level == 'exhaustive':
            # Combine full details from both taxonomies
            causal_response = self._get_causal_taxonomy_response(query)
            domain_response = self._get_domain_taxonomy_response(query)
            
            content = f"""## Complete AI Risk Repository Taxonomy Structure

{causal_response.content}

---

{domain_response.content}"""
            
            return TaxonomyResponse(
                content=content,
                taxonomy_type="both_detailed",
                source="AI Risk Repository Preprint"
            )
        else:
            return self._get_both_taxonomies_response(query)