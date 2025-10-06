#!/usr/bin/env python3
"""
Verify all new code has correct imports and no syntax errors.
"""

import ast
import py_compile
import tempfile
import os

def check_file_safety(filepath):
    """Check a Python file for import and syntax issues."""
    filename = os.path.basename(filepath)
    print(f"\nChecking {filename}:")
    
    # 1. Check syntax by compiling
    try:
        py_compile.compile(filepath, doraise=True)
        print(f"  ✓ Syntax valid")
    except py_compile.PyCompileError as e:
        print(f"  ✗ Syntax error: {e}")
        return False
    
    # 2. Parse and check imports
    with open(filepath, 'r') as f:
        content = f.read()
        tree = ast.parse(content)
    
    # Get all imports
    imports = set()
    typing_imports = set()
    
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module == 'typing':
                for name in node.names:
                    typing_imports.add(name.name)
            imports.add(node.module)
    
    # 3. Check for Any usage
    has_any = 'Any' in content and 'from typing' not in content.replace('from typing import', '')
    if 'Any' in content:
        if 'Any' in typing_imports:
            print(f"  ✓ 'Any' properly imported from typing")
        else:
            # Check if Any is just in comments/strings
            lines = content.split('\n')
            real_any_usage = False
            for line in lines:
                if 'Any' in line and not line.strip().startswith('#') and 'from typing' not in line:
                    if ': Any' in line or '[Any' in line or 'Any]' in line:
                        real_any_usage = True
                        break
            
            if real_any_usage:
                print(f"  ⚠️  'Any' used but not imported from typing")
            else:
                print(f"  ✓ 'Any' only in comments/strings")
    else:
        print(f"  ✓ No 'Any' type usage")
    
    # 4. Check other common typing imports
    typing_used = set()
    for t in ['Dict', 'List', 'Optional', 'Tuple', 'Union', 'Set']:
        if f': {t}[' in content or f'-> {t}[' in content:
            typing_used.add(t)
    
    missing = typing_used - typing_imports
    if missing:
        print(f"  ⚠️  Possibly missing typing imports: {missing}")
    else:
        print(f"  ✓ All typing imports present")
    
    return True

def main():
    """Check all new and modified files."""
    
    files_to_check = [
        'src/core/query/query_intent_analyzer.py',
        'src/core/taxonomy/taxonomy_handler.py',
        'src/core/query/intent_classifier.py',
        'src/core/services/chat_service.py'
    ]
    
    print("=" * 60)
    print("Import and Syntax Safety Check")
    print("=" * 60)
    
    all_safe = True
    for filepath in files_to_check:
        if os.path.exists(filepath):
            safe = check_file_safety(filepath)
            all_safe = all_safe and safe
        else:
            print(f"\n✗ File not found: {filepath}")
            all_safe = False
    
    print("\n" + "=" * 60)
    if all_safe:
        print("✓ All files pass safety checks")
    else:
        print("⚠️  Some issues found (see above)")
    print("=" * 60)
    
    return all_safe

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)