#!/usr/bin/env python3
"""
Chunk the extracted preprint text and index it into ChromaDB.
Creates overlapping chunks with section metadata.
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Any
import hashlib
from datetime import datetime

def identify_section(text: str, line_num: int, lines: List[str]) -> str:
    """Identify which section a chunk belongs to based on content and position."""
    
    # Look for section headers in previous lines
    section = "Unknown"
    
    # Check previous 50 lines for section headers
    start = max(0, line_num - 50)
    for i in range(start, line_num):
        line = lines[i].strip()
        
        # Major sections
        if re.match(r'^(Abstract|Introduction|Background|Methods|Results|Discussion|Conclusion|References)', line, re.IGNORECASE):
            section = line
            break
        elif 'PRISMA' in line:
            section = "Methodology - PRISMA"
        elif 'Search strategy' in line:
            section = "Methodology - Search Strategy"
        elif 'Screening' in line and 'criteria' in line.lower():
            section = "Methodology - Screening"
        elif 'Limitations' in line:
            section = "Limitations and Future Work"
        elif 'Domain Taxonomy' in line:
            section = "Domain Taxonomy"
        elif 'Causal Taxonomy' in line:
            section = "Causal Taxonomy"
        elif 'Literature' in line and ('Review' in line or 'Synthesis' in line):
            section = "Literature Review"
        elif 'Weidinger' in line or 'Gabriel' in line or 'Yampolskiy' in line:
            section = "Comparative Analysis"
        elif 'Table' in line and re.search(r'\d+', line):
            section = f"Table - {line}"
        elif 'Figure' in line and re.search(r'\d+', line):
            section = f"Figure - {line}"
    
    return section

def create_chunks(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[Dict[str, Any]]:
    """Create overlapping chunks from the text with metadata."""
    
    chunks = []
    lines = text.split('\n')
    
    # Join lines into paragraphs
    paragraphs = []
    current_para = []
    
    for line in lines:
        if line.strip() == '' and current_para:
            paragraphs.append(' '.join(current_para))
            current_para = []
        elif line.strip():
            current_para.append(line.strip())
    
    if current_para:
        paragraphs.append(' '.join(current_para))
    
    # Create chunks
    current_chunk = []
    current_size = 0
    chunk_id = 0
    
    for i, para in enumerate(paragraphs):
        para_words = para.split()
        para_size = len(para_words)
        
        if current_size + para_size > chunk_size and current_chunk:
            # Save current chunk
            chunk_text = ' '.join(current_chunk)
            
            # Identify section
            section = identify_section(chunk_text, i, lines)
            
            # Create chunk metadata
            chunk_data = {
                'id': f'PREPRINT-{chunk_id:04d}',
                'content': chunk_text,
                'metadata': {
                    'source': 'AI_Risk_Repository_Preprint',
                    'section': section,
                    'chunk_id': chunk_id,
                    'word_count': len(chunk_text.split()),
                    'char_count': len(chunk_text),
                    'type': 'preprint_content',
                    'indexed_at': datetime.now().isoformat()
                }
            }
            
            # Add content-specific metadata
            if 'PRISMA' in chunk_text:
                chunk_data['metadata']['content_type'] = 'methodology'
                chunk_data['metadata']['methodology_type'] = 'PRISMA'
            elif 'limitation' in chunk_text.lower():
                chunk_data['metadata']['content_type'] = 'limitations'
            elif 'future' in chunk_text.lower() and 'work' in chunk_text.lower():
                chunk_data['metadata']['content_type'] = 'future_work'
            elif 'Weidinger' in chunk_text or 'Gabriel' in chunk_text:
                chunk_data['metadata']['content_type'] = 'comparative_analysis'
            elif re.search(r'\d+\s*%', chunk_text):
                chunk_data['metadata']['content_type'] = 'statistical_analysis'
            elif 'Table' in chunk_text or '[TABLE]' in chunk_text:
                chunk_data['metadata']['content_type'] = 'table'
            elif 'Figure' in chunk_text:
                chunk_data['metadata']['content_type'] = 'figure'
            else:
                chunk_data['metadata']['content_type'] = 'general'
            
            chunks.append(chunk_data)
            
            # Start new chunk with overlap
            if overlap > 0:
                overlap_words = ' '.join(current_chunk).split()[-overlap:]
                current_chunk = overlap_words + para_words
                current_size = len(overlap_words) + para_size
            else:
                current_chunk = para_words
                current_size = para_size
            
            chunk_id += 1
        else:
            current_chunk.extend(para_words)
            current_size += para_size
    
    # Add final chunk
    if current_chunk:
        chunk_text = ' '.join(current_chunk)
        section = identify_section(chunk_text, len(paragraphs), lines)
        
        chunks.append({
            'id': f'PREPRINT-{chunk_id:04d}',
            'content': chunk_text,
            'metadata': {
                'source': 'AI_Risk_Repository_Preprint',
                'section': section,
                'chunk_id': chunk_id,
                'word_count': len(chunk_text.split()),
                'char_count': len(chunk_text),
                'type': 'preprint_content',
                'indexed_at': datetime.now().isoformat()
            }
        })
    
    return chunks

def save_chunks_as_snippets(chunks: List[Dict[str, Any]], output_dir: Path):
    """Save chunks as individual snippet files for the system."""
    
    output_dir.mkdir(exist_ok=True)
    
    for chunk in chunks:
        # Create RID-style filename
        rid = f"RID-PREP-{chunk['metadata']['chunk_id']:04d}"
        output_file = output_dir / f"{rid}.txt"
        
        # Format content like existing snippets
        content = f"""Repository ID: {rid}
Source: AI_Risk_Repository_Preprint.docx
Section: {chunk['metadata']['section']}
Content Type: {chunk['metadata'].get('content_type', 'general')}
Word Count: {chunk['metadata']['word_count']}

Content:
{chunk['content']}"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
    
    print(f"Saved {len(chunks)} chunks as snippet files")

def main():
    # Load the extracted preprint text
    input_path = Path('/Users/davidturturean/Documents/Codingprojects/airi-chatbot-class/data/info_files/preprint_full.txt')
    
    if not input_path.exists():
        print(f"Error: Extracted text not found at {input_path}")
        print("Please run extract_preprint_simple.py first")
        return
    
    print(f"Loading extracted text from: {input_path}")
    with open(input_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Skip the header we added
    if text.startswith("AI RISK REPOSITORY PREPRINT"):
        lines = text.split('\n')
        text = '\n'.join(lines[3:])  # Skip first 3 lines
    
    print(f"Text loaded: {len(text):,} characters")
    
    # Create chunks
    print("\nCreating chunks...")
    chunks = create_chunks(text, chunk_size=800, overlap=100)
    print(f"Created {len(chunks)} chunks")
    
    # Analyze chunk distribution
    sections = {}
    content_types = {}
    
    for chunk in chunks:
        section = chunk['metadata']['section']
        content_type = chunk['metadata'].get('content_type', 'general')
        
        sections[section] = sections.get(section, 0) + 1
        content_types[content_type] = content_types.get(content_type, 0) + 1
    
    print("\nChunk distribution by section:")
    for section, count in sorted(sections.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {section}: {count}")
    
    print("\nChunk distribution by content type:")
    for ctype, count in sorted(content_types.items(), key=lambda x: x[1], reverse=True):
        print(f"  {ctype}: {count}")
    
    # Save chunks as snippet files
    snippet_dir = Path('/Users/davidturturean/Documents/Codingprojects/airi-chatbot-class/data/doc_snippets')
    save_chunks_as_snippets(chunks, snippet_dir)
    
    # Also save chunks as JSON for reference
    json_path = Path('/Users/davidturturean/Documents/Codingprojects/airi-chatbot-class/data/preprint_chunks.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(chunks, f, indent=2)
    print(f"\nChunks saved to: {json_path}")

if __name__ == "__main__":
    main()