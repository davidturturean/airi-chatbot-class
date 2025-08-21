#!/usr/bin/env python3
"""
Simple extraction of text from the AI Risk Repository Preprint DOCX file.
"""

import docx2txt
from pathlib import Path
import re

def main():
    # Path to the DOCX file
    docx_path = Path('/Users/davidturturean/Documents/Codingprojects/airi-chatbot-class/data/info_files/AI_Risk_Repository_Preprint.docx')
    
    if not docx_path.exists():
        print(f"Error: File not found at {docx_path}")
        return
    
    print(f"Extracting text from: {docx_path}")
    print(f"File size: {docx_path.stat().st_size / 1024 / 1024:.2f} MB")
    
    # Extract text using docx2txt
    print("\nExtracting text content...")
    text_content = docx2txt.process(str(docx_path))
    
    # Clean up the text
    # Remove excessive whitespace
    text_content = re.sub(r'\n{4,}', '\n\n\n', text_content)
    text_content = re.sub(r' {2,}', ' ', text_content)
    text_content = text_content.strip()
    
    # Save to file
    output_path = Path('/Users/davidturturean/Documents/Codingprojects/airi-chatbot-class/data/info_files/preprint_full.txt')
    
    print(f"\nWriting to: {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("AI RISK REPOSITORY PREPRINT - FULL TEXT EXTRACTION\n")
        f.write("=" * 80 + "\n\n")
        f.write(text_content)
    
    # Calculate statistics
    word_count = len(text_content.split())
    char_count = len(text_content)
    lines = text_content.split('\n')
    
    print(f"\nExtraction complete!")
    print(f"- Lines extracted: {len(lines):,}")
    print(f"- Words extracted: {word_count:,}")
    print(f"- Characters extracted: {char_count:,}")
    print(f"- Output file size: {output_path.stat().st_size / 1024:.2f} KB")
    
    # Also save a raw version
    raw_output_path = Path('/Users/davidturturean/Documents/Codingprojects/airi-chatbot-class/data/info_files/preprint_raw.txt')
    with open(raw_output_path, 'w', encoding='utf-8') as f:
        f.write(text_content)
    
    print(f"- Raw text saved to: {raw_output_path}")
    
    # Show first 1000 characters as preview
    print("\n" + "=" * 80)
    print("PREVIEW OF EXTRACTED TEXT:")
    print("=" * 80)
    print(text_content[:1000])
    print("..." if len(text_content) > 1000 else "")

if __name__ == "__main__":
    main()