"""
Schema definition for the AI Risk Repository database.
"""
from typing import Dict, List, Any
from .base_schema import BaseSchema, ColumnDefinition

class RiskSchema(BaseSchema):
    """Schema for AI Risk Repository entries."""
    
    def __init__(self):
        super().__init__(
            name="ai_risks",
            table_name="risks",
            id_prefix="RID",
            description="AI Risk Repository containing categorized AI risks"
        )
    
    def get_columns(self) -> List[ColumnDefinition]:
        """Define columns for the risks table."""
        return [
            ColumnDefinition("rid", "VARCHAR", is_primary_key=True, description="Risk ID"),
            ColumnDefinition("title", "VARCHAR", is_indexed=True, description="Risk title"),
            ColumnDefinition("domain", "VARCHAR", is_indexed=True, description="Primary domain (1-7)"),
            ColumnDefinition("subdomain", "VARCHAR", is_indexed=True, description="Subdomain"),
            ColumnDefinition("risk_category", "VARCHAR", is_indexed=True, description="Risk category"),
            ColumnDefinition("description", "TEXT", is_searchable=True, description="Risk description"),
            ColumnDefinition("entity", "INTEGER", is_indexed=True, description="Entity (1=Human, 2=AI)"),
            ColumnDefinition("intent", "INTEGER", is_indexed=True, description="Intent (1=Intentional, 2=Unintentional)"),
            ColumnDefinition("timing", "INTEGER", is_indexed=True, description="Timing (1=Pre-deployment, 2=Post-deployment, 3=Other)"),
            ColumnDefinition("year", "INTEGER", is_indexed=True, description="Publication year"),
            ColumnDefinition("authors", "VARCHAR", is_searchable=True, description="Authors or source"),
            ColumnDefinition("row_number", "INTEGER", description="Original row number in source"),
            ColumnDefinition("source_file", "VARCHAR", description="Source file path"),
        ]
    
    def extract_row_data(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data from Excel row to database row."""
        # Map Excel columns to database columns
        return {
            "rid": row.get("rid", ""),
            "title": row.get("title", ""),
            "domain": row.get("domain", ""),
            "subdomain": row.get("subdomain", "").replace("Sub-domain: ", ""),
            "risk_category": row.get("risk_category", ""),
            "description": row.get("content", row.get("description", "")),
            "entity": self._parse_entity(row.get("entity", "")),
            "intent": self._parse_intent(row.get("intent", "")),
            "timing": self._parse_timing(row.get("timing", "")),
            "year": self._extract_year(row),
            "authors": row.get("authors", ""),
            "row_number": row.get("row", 0),
            "source_file": row.get("source", ""),
        }
    
    def _parse_entity(self, entity_str: str) -> int:
        """Parse entity string to integer."""
        if "1" in str(entity_str) or "Human" in str(entity_str):
            return 1
        elif "2" in str(entity_str) or "AI" in str(entity_str):
            return 2
        return 0
    
    def _parse_intent(self, intent_str: str) -> int:
        """Parse intent string to integer."""
        if "1" in str(intent_str) or "Intentional" in str(intent_str):
            return 1
        elif "2" in str(intent_str) or "Unintentional" in str(intent_str):
            return 2
        return 0
    
    def _parse_timing(self, timing_str: str) -> int:
        """Parse timing string to integer."""
        if "1" in str(timing_str) or "Pre-deployment" in str(timing_str):
            return 1
        elif "2" in str(timing_str) or "Post-deployment" in str(timing_str):
            return 2
        elif "3" in str(timing_str) or "Other" in str(timing_str):
            return 3
        return 0
    
    def _extract_year(self, row: Dict[str, Any]) -> int:
        """Extract year from various possible fields."""
        # Try different year fields
        for field in ["year", "publication_year", "date"]:
            if field in row and row[field]:
                try:
                    return int(str(row[field])[:4])
                except:
                    pass
        
        # Try to extract from title or description
        import re
        text = f"{row.get('title', '')} {row.get('description', '')}"
        year_match = re.search(r'20\d{2}|19\d{2}', text)
        if year_match:
            return int(year_match.group())
        
        return 0
    
    def validate_row(self, row: Dict[str, Any]) -> bool:
        """Validate that row has minimum required fields."""
        return bool(row.get("rid") and (row.get("title") or row.get("description")))