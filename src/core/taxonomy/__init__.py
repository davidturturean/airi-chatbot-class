"""
Taxonomy systems for content organization and structure.
"""

# Import scqa_taxonomy only if langchain is available
try:
    from .scqa_taxonomy import (
        SCQAComponent,
        ContentType,
        SCQAStructure,
        SCQAAnalyzer,
        SCQATaxonomyManager,
        scqa_manager
    )
    
    __all__ = [
        'SCQAComponent',
        'ContentType', 
        'SCQAStructure',
        'SCQAAnalyzer',
        'SCQATaxonomyManager',
        'scqa_manager'
    ]
except ImportError:
    # If langchain is not available, don't expose SCQA functionality
    # But allow taxonomy_handler to still work
    __all__ = []