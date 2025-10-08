#!/usr/bin/env python3
"""
Quick test script to verify Excel formatting extraction is working.
Tests the _extract_cell_formatting function directly.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.api.routes.excel_viewer import _extract_cell_formatting

def test_formatting_extraction():
    """Test formatting extraction on the AI Risk Repository file."""

    # Path to test Excel file
    excel_file = Path(__file__).parent / "data/info_files/The_AI_Risk_Repository_V3_26_03_2025.xlsx"

    if not excel_file.exists():
        print(f"❌ Test file not found: {excel_file}")
        return False

    print(f"Testing formatting extraction on: {excel_file.name}")
    print("-" * 80)

    # Test formatting extraction for first 100 rows
    try:
        # Get first sheet name
        import openpyxl
        workbook = openpyxl.load_workbook(str(excel_file), read_only=True, data_only=True)
        sheet_names = workbook.sheetnames
        workbook.close()

        print(f"\nFound {len(sheet_names)} sheets: {sheet_names[:3]}{'...' if len(sheet_names) > 3 else ''}")

        # Test first sheet
        test_sheet = sheet_names[0]
        print(f"\nTesting sheet: '{test_sheet}'")

        # Extract formatting
        formatting = _extract_cell_formatting(
            excel_file,
            test_sheet,
            offset=0,
            max_rows=100
        )

        print(f"\n✅ Formatting extraction successful!")
        print(f"   - Found {len(formatting)} formatted cells")

        if formatting:
            # Show sample formatting
            print(f"\n📊 Sample formatted cells:")
            for i, (key, fmt) in enumerate(list(formatting.items())[:5]):
                print(f"   - Cell {key}: {fmt}")

            # Count different formatting types
            has_bg_color = sum(1 for f in formatting.values() if 'bgColor' in f)
            has_font_color = sum(1 for f in formatting.values() if 'fontColor' in f)
            has_bold = sum(1 for f in formatting.values() if f.get('bold'))
            has_borders = sum(1 for f in formatting.values() if 'borders' in f)

            print(f"\n📈 Formatting statistics:")
            print(f"   - Background colors: {has_bg_color}")
            print(f"   - Font colors: {has_font_color}")
            print(f"   - Bold text: {has_bold}")
            print(f"   - Borders: {has_borders}")
        else:
            print(f"\n⚠️  No formatted cells found in first 100 rows")
            print(f"   This is normal if the sheet has no colors, bold, or borders")

        return True

    except Exception as e:
        print(f"\n❌ Error during formatting extraction:")
        print(f"   {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 80)
    print("Excel Formatting Extraction Test")
    print("=" * 80)

    success = test_formatting_extraction()

    print("\n" + "=" * 80)
    if success:
        print("✅ Test completed successfully!")
    else:
        print("❌ Test failed!")
    print("=" * 80)

    sys.exit(0 if success else 1)
