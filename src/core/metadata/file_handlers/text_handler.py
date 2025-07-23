"""
Text and Markdown file handler.
"""
from pathlib import Path
from typing import Dict, List, Any, Optional
import re
from .base_handler import BaseFileHandler
from ....config.logging import get_logger

logger = get_logger(__name__)

class TextHandler(BaseFileHandler):
    """Handler for text-based files (.txt, .md)."""
    
    def __init__(self):
        super().__init__()
        self.supported_extensions = ['.txt', '.md', '.markdown']
    
    def can_handle(self, file_path: Path) -> bool:
        """Check if this is a text file."""
        return file_path.suffix.lower() in self.supported_extensions
    
    def extract_data(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extract structured data from text files."""
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not content.strip():
                logger.warning(f"Text file is empty: {file_path}")
                return []
            
            # Try different extraction strategies
            extracted_data = []
            
            # Strategy 1: Look for tables in markdown
            if file_path.suffix.lower() in ['.md', '.markdown']:
                tables = self._extract_markdown_tables(content)
                extracted_data.extend(tables)
            
            # Strategy 2: Look for structured lists (e.g., "ID: value" patterns)
            structured_items = self._extract_structured_items(content)
            if structured_items:
                extracted_data.append(structured_items)
            
            # Strategy 3: Extract sections as records
            sections = self._extract_sections(content, file_path.suffix.lower())
            if sections:
                extracted_data.append(sections)
            
            # If no structured data found, create a simple text table
            if not extracted_data:
                lines = content.strip().split('\n')
                data = []
                for i, line in enumerate(lines):
                    if line.strip():
                        data.append({
                            "line_number": i + 1,
                            "content": line.strip(),
                            "length": len(line.strip())
                        })
                
                if data:
                    extracted_data.append({
                        "table_name": self.sanitize_table_name(f"{file_path.stem}_lines"),
                        "data": data,
                        "metadata": {
                            "source_file": str(file_path),
                            "extraction_method": "line_by_line"
                        }
                    })
            
            return extracted_data
            
        except Exception as e:
            logger.error(f"Error extracting data from text file {file_path}: {str(e)}")
            return []
    
    def _extract_markdown_tables(self, content: str) -> List[Dict[str, Any]]:
        """Extract tables from markdown content."""
        tables = []
        
        # Find markdown tables using regex
        table_pattern = r'\|(.+)\|\n\|[\s\-\|]+\|\n((?:\|.+\|\n?)+)'
        matches = re.finditer(table_pattern, content, re.MULTILINE)
        
        for i, match in enumerate(matches):
            header_line = match.group(1)
            data_lines = match.group(2).strip().split('\n')
            
            # Parse headers
            headers = [h.strip() for h in header_line.split('|') if h.strip()]
            headers = [self._clean_column_name(h) for h in headers]
            
            # Parse data rows
            data = []
            for line in data_lines:
                values = [v.strip() for v in line.split('|') if v.strip()]
                if len(values) == len(headers):
                    row = dict(zip(headers, values))
                    data.append(row)
            
            if data:
                tables.append({
                    "table_name": self.sanitize_table_name(f"table_{i+1}"),
                    "data": data,
                    "metadata": {
                        "extraction_method": "markdown_table",
                        "table_index": i + 1
                    }
                })
        
        return tables
    
    def _extract_structured_items(self, content: str) -> Optional[Dict[str, Any]]:
        """Extract structured items like 'Key: Value' patterns."""
        # Pattern for structured data (e.g., "RID-001: Description")
        patterns = [
            r'^([A-Z]{2,}-\d+):\s*(.+)$',  # ID pattern (RID-001: ...)
            r'^(\w+):\s*(.+)$',  # Simple key-value
            r'^-\s*(\w+):\s*(.+)$',  # Bullet list key-value
        ]
        
        all_items = []
        
        for pattern in patterns:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                key = match.group(1).strip()
                value = match.group(2).strip()
                
                # Check if this looks like an ID
                if re.match(r'^[A-Z]{2,}-\d+$', key):
                    all_items.append({
                        "id": key,
                        "content": value,
                        "type": "structured_id"
                    })
                else:
                    all_items.append({
                        "key": self._clean_column_name(key),
                        "value": value,
                        "type": "key_value"
                    })
        
        if all_items:
            table_name = "structured_data"
            return {
                "table_name": self.sanitize_table_name(table_name),
                "data": all_items,
                "metadata": {
                    "extraction_method": "structured_patterns",
                    "item_count": len(all_items)
                }
            }
        
        return None
    
    def _extract_sections(self, content: str, file_type: str) -> Optional[Dict[str, Any]]:
        """Extract sections from the document."""
        sections = []
        
        if file_type in ['.md', '.markdown']:
            # Extract markdown sections
            section_pattern = r'^(#{1,6})\s+(.+)$'
            lines = content.split('\n')
            
            current_section = None
            current_content = []
            
            for line in lines:
                match = re.match(section_pattern, line)
                if match:
                    # Save previous section
                    if current_section:
                        sections.append({
                            "level": current_section['level'],
                            "title": current_section['title'],
                            "content": '\n'.join(current_content).strip()
                        })
                    
                    # Start new section
                    current_section = {
                        'level': len(match.group(1)),
                        'title': match.group(2).strip()
                    }
                    current_content = []
                else:
                    current_content.append(line)
            
            # Save last section
            if current_section:
                sections.append({
                    "level": current_section['level'],
                    "title": current_section['title'],
                    "content": '\n'.join(current_content).strip()
                })
        
        if sections:
            return {
                "table_name": self.sanitize_table_name("sections"),
                "data": sections,
                "metadata": {
                    "extraction_method": "section_extraction",
                    "section_count": len(sections)
                }
            }
        
        return None
    
    def _clean_column_name(self, name: str) -> str:
        """Clean column name for SQL compatibility."""
        import re
        name = re.sub(r'[^a-zA-Z0-9_\s]', '', name)
        name = name.replace(' ', '_')
        name = re.sub(r'_+', '_', name)
        name = name.strip('_').lower()
        
        if not name:
            return "unnamed"
        if not name[0].isalpha():
            name = f"col_{name}"
        
        return name