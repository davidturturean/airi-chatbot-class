"""
Citation service for handling document references and snippets.
"""
import os
import hashlib
import re
from typing import List
from langchain.docstore.document import Document

from ...config.logging import get_logger
from ...config.settings import settings
from ...core.storage.snippet_database import snippet_db
from datetime import datetime

logger = get_logger(__name__)

class CitationService:
    """Handles citation generation and snippet management with RID-based citations."""
    
    def __init__(self):
        self.snippets_dir = settings.DOC_SNIPPETS_DIR
        # Ensure snippets directory exists for legacy support
        self.snippets_dir.mkdir(parents=True, exist_ok=True)
        
        # RID to citation mapping for deterministic citation replacement
        self.rid_citation_map = {}
        
        # Current session ID (will be set per request)
        self.current_session_id = None
    
    def enhance_response_with_citations(self, response: str, docs: List[Document], session_id: str = None) -> str:
        """
        Add RID-based citations to the response text with inline highlighting.
        
        Args:
            response: Generated response text
            docs: Source documents
            session_id: Session ID for storing snippets
            
        Returns:
            Response with enhanced RID-based citations and highlighting
        """
        if not docs:
            return response
        
        # Set current session for this request
        self.current_session_id = session_id
        
        # Build RID citation mapping
        self.rid_citation_map = {}
        for doc in docs:
            rid = doc.metadata.get('rid', None)
            if rid:
                citation = self._format_rid_citation(doc)
                self.rid_citation_map[rid] = citation
                
                # Save snippet to database if session ID provided
                if session_id:
                    self._save_rid_snippet_to_db(doc, rid, session_id)
                else:
                    # Fall back to file system for legacy support
                    self._save_rid_snippet(doc, rid)
        
        # Replace RID placeholders and legacy patterns
        enhanced_response = self._replace_rid_citations(response, docs)
        
        # Add inline highlighting for supported claims
        enhanced_response = self._add_inline_highlighting(enhanced_response, docs)
        
        # Apply section-level citation validation
        enhanced_response = self._validate_section_citations(enhanced_response, docs)
        
        logger.info(f"RID citation enhancement complete. RIDs processed: {len(self.rid_citation_map)}")
        return enhanced_response
    
    def _replace_rid_citations(self, response: str, docs: List[Document]) -> str:
        """Replace RID placeholders and legacy section references with proper citations."""
        enhanced_response = response
        
        # First, build a complete RID to document mapping from all docs
        rid_to_doc = {}
        for doc in docs:
            rid = doc.metadata.get('rid')
            if rid:
                rid_to_doc[rid] = doc
        
        # Replace any RID-##### patterns with proper citations (single comprehensive pass)
        import re
        
        # Single pattern to catch all variations, prioritizing parenthetical ones
        # This pattern matches: (RID-12345) or RID-12345, but captures the RID number
        rid_pattern = r'(?:\()?RID-(\d{5})(?:\))?'
        
        def replace_rid(match):
            # Extract the RID part (RID-##### format)
            rid = f"RID-{match.group(1)}"
            
            # Try to get from existing citation map first
            if rid in self.rid_citation_map:
                logger.info(f"✓ Using existing citation for {rid}")
                return self.rid_citation_map[rid]
            
            # If not in map but we have the document, create citation on-the-fly
            if rid in rid_to_doc:
                doc = rid_to_doc[rid]
                citation = self._format_rid_citation(doc)
                self.rid_citation_map[rid] = citation
                logger.info(f"✓ Created on-the-fly citation for {rid}")
                return citation
            
            # If RID not found in docs, convert to clickable link anyway
            logger.warning(f"RID {rid} not found in documents but making clickable")
            return f"[{rid}](/snippet/{rid})"
        
        # Apply the pattern once
        before_count = len(re.findall(rid_pattern, enhanced_response))
        enhanced_response = re.sub(rid_pattern, replace_rid, enhanced_response)
        after_count = len(re.findall(rid_pattern, enhanced_response))
        if before_count > 0:
            logger.info(f"✓ RID pattern found {before_count} matches, {before_count - after_count} replaced")
        
        # Handle legacy patterns (SECTION X, Document X) for backward compatibility
        for i, doc in enumerate(docs, 1):
            rid = doc.metadata.get('rid')
            if not rid:
                continue
                
            citation = self.rid_citation_map.get(rid, f"[Source {i}]")
            
            # Replace various legacy patterns
            patterns = [
                f"SECTION {i}",
                f"Source {i}",
                f"Document {i}",
                f"Entry {i}"
            ]
            
            for pattern in patterns:
                if pattern in enhanced_response:
                    enhanced_response = enhanced_response.replace(pattern, citation)
                    logger.info(f"✓ Replaced legacy pattern '{pattern}' with RID citation")
        
        # If no citations were added through pattern replacement, append them
        if self.rid_citation_map and not any(rid in enhanced_response for rid in self.rid_citation_map.keys()):
            logger.info("No citation patterns found - appending citations to response")
            citations_list = []
            for rid, citation in self.rid_citation_map.items():
                citations_list.append(f"{rid}: {citation}")
            
            if citations_list:
                enhanced_response += "\n\n**Sources:**\n" + "\n".join(f"• {cite}" for cite in citations_list)
                logger.info(f"✓ Appended {len(citations_list)} citations to response")
        
        return enhanced_response
    
    def _add_inline_highlighting(self, response: str, docs: List[Document]) -> str:
        """Add bold highlighting to phrases that directly reference source content."""
        # For now, implement basic highlighting
        # Future enhancement: use fuzzy matching to find exact phrases from sources
        return response  # Placeholder for inline highlighting feature
    
    def _validate_section_citations(self, response: str, docs: List[Document]) -> str:
        """Validate that each paragraph has proper citations and avoid RID overuse."""
        import re
        
        # Split response into paragraphs
        paragraphs = [p.strip() for p in response.split('\n\n') if p.strip()]
        
        # Track RID usage to prevent overuse
        rid_usage_count = {}
        available_rids = [doc.metadata.get('rid') for doc in docs if doc.metadata.get('rid')]
        
        # Count existing RID usage
        for paragraph in paragraphs:
            for rid in available_rids:
                if rid and rid in paragraph:
                    rid_usage_count[rid] = rid_usage_count.get(rid, 0) + 1
        
        # Validate each paragraph
        validated_paragraphs = []
        for i, paragraph in enumerate(paragraphs):
            # Skip source lists and metadata
            if paragraph.startswith('**Sources:**') or paragraph.startswith('•'):
                validated_paragraphs.append(paragraph)
                continue
                
            # Check if paragraph has citations
            has_citation = any(rid in paragraph for rid in available_rids if rid)
            
            # If no citation and it's a substantive paragraph, add one
            if not has_citation and len(paragraph) > 100 and not paragraph.startswith('The AI Risk Repository'):
                # Find least-used RID that hasn't been overused
                best_rid = self._find_best_rid_for_paragraph(paragraph, available_rids, rid_usage_count)
                if best_rid:
                    # Add citation at the end of paragraph if it doesn't have one
                    if not paragraph.endswith('.'):
                        paragraph += '.'
                    
                    # Create enhanced citation instead of raw RID
                    if best_rid in self.rid_citation_map:
                        enhanced_citation = self.rid_citation_map[best_rid]
                    else:
                        enhanced_citation = f"[{best_rid}](/snippet/{best_rid})"
                    
                    paragraph += f" {enhanced_citation}"
                    rid_usage_count[best_rid] = rid_usage_count.get(best_rid, 0) + 1
                    logger.info(f"Added enhanced citation {best_rid} to paragraph {i+1}")
            
            validated_paragraphs.append(paragraph)
        
        # Check for RID overuse and redistribute if needed
        overused_rids = [rid for rid, count in rid_usage_count.items() if count > 2]
        if overused_rids:
            logger.info(f"Detected overused RIDs: {overused_rids}")
            validated_paragraphs = self._redistribute_overused_rids(validated_paragraphs, overused_rids, available_rids)
        
        return '\n\n'.join(validated_paragraphs)
    
    def _find_best_rid_for_paragraph(self, paragraph: str, available_rids: List[str], usage_count: dict) -> str:
        """Find the best RID to cite for a paragraph based on usage and relevance."""
        # Simple heuristic: use least-used RID first
        sorted_rids = sorted(available_rids, key=lambda rid: usage_count.get(rid, 0))
        return sorted_rids[0] if sorted_rids else None
    
    def _redistribute_overused_rids(self, paragraphs: List[str], overused_rids: List[str], available_rids: List[str]) -> List[str]:
        """Redistribute overused RIDs to achieve better citation balance."""
        # For now, just log the issue - full redistribution would be complex
        logger.info(f"Citation redistribution needed for RIDs: {overused_rids}")
        return paragraphs
    
    def _format_rid_citation(self, doc: Document) -> str:
        """Format a citation using the document's RID."""
        rid = doc.metadata.get('rid', 'RID-UNKNOWN')
        file_type = doc.metadata.get('file_type', '')
        
        # Create human-readable citation text based on document type
        if 'ai_risk_entry' in file_type:
            title = doc.metadata.get('title', 'AI Risk Entry')
            domain = doc.metadata.get('domain', '')
            if domain and domain != 'Unspecified':
                citation_text = f"{title} (Domain: {domain})"
            else:
                citation_text = title
        elif 'domain_summary' in file_type:
            domain = doc.metadata.get('domain', 'Unknown Domain')
            citation_text = f"AI Risk Domain: {domain}"
        elif 'excel' in file_type:
            sheet = doc.metadata.get('sheet', 'Unknown Sheet')
            row = doc.metadata.get('row', '')
            if row:
                citation_text = f"MIT AI Repository, {sheet}, Row {row}"
            else:
                citation_text = f"MIT AI Repository, {sheet}"
        else:
            # Generic citation
            source = doc.metadata.get('source', 'Unknown Source')
            filename = os.path.basename(source)
            if 'AI_Risk' in filename:
                citation_text = "AI Risk Repository Document"
            else:
                citation_text = filename.replace('_', ' ').replace('-', ' ')[:30]
        
        return f"[{citation_text}](/snippet/{rid})"
    
    def _save_rid_snippet(self, doc: Document, rid: str) -> None:
        """Save document snippet using RID for easy retrieval (legacy file system support)."""
        snippet_path = self.snippets_dir / f"{rid}.txt"
        
        try:
            with open(snippet_path, 'w', encoding='utf-8') as f:
                f.write(f"Repository ID: {rid}\n")
                f.write(f"Source: {doc.metadata.get('source', 'Unknown')}\n")
                
                # Add all metadata
                for key, value in doc.metadata.items():
                    if key not in ['source', 'page_content', 'content_hash']:
                        f.write(f"{key}: {value}\n")
                
                f.write(f"\nContent:\n{doc.page_content}")
        except Exception as e:
            logger.error(f"Error saving RID snippet for {rid}: {str(e)}")
    
    def _save_rid_snippet_to_db(self, doc: Document, rid: str, session_id: str):
        """Save document content as JSON snippet in database."""
        try:
            metadata = doc.metadata or {}
            content = doc.page_content
            
            # Parse title from content if not in metadata
            title = metadata.get('title', rid)
            if not title or title == rid:
                lines = content.split('\n')
                for line in lines:
                    if line.startswith('Title:'):
                        title = line.replace('Title:', '').strip()
                        break
            
            # Create JSON snippet
            snippet_data = {
                "rid": rid,
                "title": title,
                "content": content,
                "metadata": {
                    "domain": metadata.get('domain', ''),
                    "subdomain": metadata.get('subdomain', metadata.get('specific_domain', '')),
                    "risk_category": metadata.get('risk_category', ''),
                    "entity": self._map_entity_value(metadata.get('entity', '')),
                    "intent": self._map_intent_value(metadata.get('intent', '')),
                    "timing": self._map_timing_value(metadata.get('timing', '')),
                    "description": metadata.get('description', ''),
                    "source_file": metadata.get('url', metadata.get('source_file', '')),
                    "row_number": metadata.get('row', None)
                },
                "highlights": metadata.get('search_terms', []),
                "created_at": datetime.now().isoformat()
            }
            
            # Save to database
            success = snippet_db.save_snippet(session_id, rid, snippet_data)
            if success:
                logger.info(f"Saved snippet {rid} to database for session {session_id}")
            else:
                logger.error(f"Failed to save snippet {rid} to database")
                # Fall back to file system
                self._save_rid_snippet(doc, rid)
            
        except Exception as e:
            logger.error(f"Error saving snippet to database for {rid}: {str(e)}")
            # Fall back to file system
            self._save_rid_snippet(doc, rid)
    
    def _map_entity_value(self, entity: str) -> str:
        """Map numeric entity values to readable strings."""
        entity_map = {
            '1': 'Human',
            '2': 'AI',
            '3': 'Human & AI'
        }
        return entity_map.get(str(entity), entity)
    
    def _map_intent_value(self, intent: str) -> str:
        """Map numeric intent values to readable strings."""
        intent_map = {
            '1': 'Intentional',
            '2': 'Unintentional'
        }
        return intent_map.get(str(intent), intent)
    
    def _map_timing_value(self, timing: str) -> str:
        """Map numeric timing values to readable strings."""
        timing_map = {
            '1': 'Pre-deployment',
            '2': 'Post-deployment'
        }
        return timing_map.get(str(timing), timing)
    
    def get_snippet_by_rid(self, rid: str, include_metadata: bool = False) -> str:
        """Get snippet content by RID."""
        snippet_path = self.snippets_dir / f"{rid}.txt"
        
        if snippet_path.exists():
            try:
                with open(snippet_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if include_metadata:
                        # This is a simplified implementation. A more robust implementation
                        # would parse the file content and return a JSON object.
                        return {
                            "content": content,
                            "file_type": "text"
                        }
                    else:
                        return content
            except Exception as e:
                logger.error(f"Error reading RID snippet {rid}: {str(e)}")
                return f"Error reading snippet {rid}: {str(e)}"
        else:
            return f"Snippet for {rid} not found"
    
    def _format_document_citation(self, doc: Document) -> str:
        """Format a citation for a document based on its type and metadata."""
        if not doc or not hasattr(doc, 'metadata'):
            return "[Unknown Source]"
        
        # Get basic metadata
        file_type = doc.metadata.get('file_type', '')
        source = doc.metadata.get('source', 'Unknown')
        
        # Create a unique ID for this document reference
        doc_id = hashlib.md5(f"{source}_{file_type}".encode()).hexdigest()[:8]
        
        # Save snippet for reference
        self._save_document_snippet(doc, doc_id)
        
        # Create appropriate citation based on file type
        if 'excel' in file_type.lower():
            return self._format_excel_citation(doc, doc_id)
        elif doc.metadata.get('citation'):
            # Use existing citation if available but add link
            citation = doc.metadata.get('citation')
            return f"[{citation}](/snippet/{doc_id})"
        else:
            # Create a clean generic citation
            filename = os.path.basename(source)
            if 'AI_Risk' in filename or 'ai_risk' in filename.lower():
                citation_text = "AI Risk Repository Document"
            else:
                # Clean filename for display
                clean_name = filename.replace('_', ' ').replace('-', ' ')
                if len(clean_name) > 30:
                    clean_name = clean_name[:30] + "..."
                citation_text = clean_name
            
            return f"[{citation_text}](/snippet/{doc_id})"
    
    def _format_excel_citation(self, doc: Document, doc_id: str) -> str:
        """Format a citation specifically for Excel files with sheet and row info."""
        sheet_name = doc.metadata.get('sheet', 'Unknown Sheet')
        row = doc.metadata.get('row', None)
        
        # Create clean, readable citation text
        if 'AI Risk Database' in sheet_name:
            if row is not None:
                citation_text = f"AI Risk Repository, Row {row}"
            else:
                citation_text = "AI Risk Repository"
        else:
            if row is not None:
                citation_text = f"MIT AI Repository, {sheet_name}, Row {row}"
            else:
                citation_text = f"MIT AI Repository, {sheet_name}"
        
        return f"[{citation_text}](/snippet/{doc_id})"
    
    def _save_document_snippet(self, doc: Document, doc_id: str) -> None:
        """Save document snippet for later reference."""
        snippet_path = self.snippets_dir / f"doc_{doc_id}.txt"
        
        try:
            with open(snippet_path, 'w') as f:
                f.write(f"Source: {doc.metadata.get('source', 'Unknown')}\\n")
                
                # Add all metadata
                for key, value in doc.metadata.items():
                    if key not in ['source', 'page_content']:
                        f.write(f"{key}: {value}\\n")
                
                f.write(f"\\nContent:\\n{doc.page_content}")
        except Exception as e:
            logger.error(f"Error saving document snippet: {str(e)}")
    
    def _clean_for_filename(self, text: str, max_length: int = 50) -> str:
        """Clean a string to make it suitable for use as a filename."""
        # Remove invalid filename characters
        clean = re.sub(r'[\\\\/*?:"<>|]', '', text)
        # Replace spaces and underscores with hyphens
        clean = re.sub(r'[\\s_]+', '-', clean)
        # Truncate to reasonable length
        return clean[:max_length]
    
    def get_snippet_content(self, snippet_id: str, include_metadata: bool = False) -> str:
        """Get snippet content by ID."""
        snippet_path = self.snippets_dir / f"doc_{snippet_id}.txt"
        
        if snippet_path.exists():
            try:
                with open(snippet_path, 'r') as f:
                    content = f.read()
                    if include_metadata:
                        # This is a simplified implementation. A more robust implementation
                        # would parse the file content and return a JSON object.
                        return {
                            "content": content,
                            "file_type": "text"
                        }
                    else:
                        return content
            except Exception as e:
                logger.error(f"Error reading snippet: {str(e)}")
                return f"Error reading snippet: {str(e)}"
        else:
            return "Snippet not found"