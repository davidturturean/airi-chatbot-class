"""
Metadata infrastructure for handling multiple databases and meta-structural queries.
"""
from .metadata_service_v2 import flexible_metadata_service as metadata_service
from .metadata_service_v2 import FlexibleMetadataService

__all__ = ['metadata_service', 'FlexibleMetadataService']