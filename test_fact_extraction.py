#!/usr/bin/env python3
"""Test fact extraction system."""

from src.core.metadata.fact_extractor import FactExtractor
from langchain.docstore.document import Document

# Test fact extraction
extractor = FactExtractor()

# Test document with 777 documents mention
test_doc = Document(
    page_content='We analyzed a total of 777 documents from the AI Risk Repository. The systematic review methodology followed PRISMA guidelines. Authors including Slattery et al and Gabriel conducted the analysis.',
    metadata={'source': 'test'}
)

facts = extractor.extract_facts(test_doc)
print('Extracted facts:')
for key, value in facts.items():
    if key != 'source':
        print(f'  {key}: {value}')

print('\n--- Testing query analysis ---')
from src.core.retrieval.multi_strategy_retriever import MultiStrategyRetriever

# Mock retriever to test query analysis
class MockRetriever:
    def _analyze_query(self, query: str):
        retriever = MultiStrategyRetriever(None, [])
        return retriever._analyze_query(query)

mock = MockRetriever()

queries = [
    "How many documents were analyzed?",
    "What systematic review methodology was used?",
    "Who are the authors?",
]

for query in queries:
    analysis = mock._analyze_query(query)
    print(f"\nQuery: {query}")
    print(f"Analysis: {analysis}")