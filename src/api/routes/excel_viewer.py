"""
Excel document viewer routes for the Interactive Reference Visualization system.
Parses Excel files and returns interactive data for the frontend viewer.
Performance target: <500ms for typical Excel files
"""
from flask import Blueprint, jsonify, request
import pandas as pd
import openpyxl
from datetime import datetime
from pathlib import Path
from ...core.storage.snippet_database import snippet_db
from ...config.logging import get_logger
from ...config.settings import settings

logger = get_logger(__name__)

# Create blueprint
excel_viewer_bp = Blueprint('excel_viewer', __name__)

# This will be injected by the app factory
chat_service = None

def init_excel_routes(chat_service_instance):
    """Initialize Excel viewer routes with service dependency."""
    global chat_service
    chat_service = chat_service_instance

@excel_viewer_bp.route('/api/document/<rid>/excel', methods=['GET'])
def get_excel_data(rid):
    """
    Parse and return Excel file data for interactive viewing.
    Performance target: <500ms
    """
    try:
        start_time = datetime.now()

        # Get session ID
        session_id = request.args.get('session_id') or request.headers.get('X-Session-ID')
        if not session_id:
            return jsonify({"error": "Session ID required"}), 400

        # Get optional parameters
        sheet_name = request.args.get('sheet')
        max_rows = int(request.args.get('max_rows', 1000))
        offset = int(request.args.get('offset', 0))

        # Get document metadata
        snippet_data = snippet_db.get_snippet(session_id, rid)
        if not snippet_data:
            return jsonify({"error": "Document not found"}), 404

        # Get file path from metadata
        source_file = snippet_data.get('metadata', {}).get('source_file', '')
        if not source_file:
            return jsonify({"error": "No source file specified"}), 404

        # Resolve file path
        file_path = _resolve_file_path(source_file)
        if not file_path or not file_path.exists():
            return jsonify({"error": f"File not found: {source_file}"}), 404

        # Parse Excel file
        excel_data = _parse_excel_file(file_path, sheet_name, max_rows, offset)

        # Add metadata
        excel_data['rid'] = rid
        excel_data['title'] = snippet_data.get('title', file_path.name)
        excel_data['metadata'] = snippet_data.get('metadata', {})

        # Calculate performance
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        if duration_ms > 500:
            logger.warning(f"Excel parsing exceeded target: {duration_ms:.2f}ms for {rid}")

        return jsonify(excel_data)

    except Exception as e:
        logger.error(f"Error parsing Excel file for {rid}: {str(e)}")
        return jsonify({"error": f"Failed to parse Excel: {str(e)}"}), 500

@excel_viewer_bp.route('/api/document/<rid>/excel/sheets', methods=['GET'])
def get_excel_sheets(rid):
    """
    Get list of sheets in an Excel file without loading full data.
    Used for quick sheet navigation.
    """
    try:
        session_id = request.args.get('session_id') or request.headers.get('X-Session-ID')
        if not session_id:
            return jsonify({"error": "Session ID required"}), 400

        snippet_data = snippet_db.get_snippet(session_id, rid)
        if not snippet_data:
            return jsonify({"error": "Document not found"}), 404

        source_file = snippet_data.get('metadata', {}).get('source_file', '')
        file_path = _resolve_file_path(source_file)

        if not file_path or not file_path.exists():
            return jsonify({"error": "File not found"}), 404

        # Get sheet names
        workbook = openpyxl.load_workbook(str(file_path), read_only=True, data_only=True)
        sheets = [
            {
                'sheet_name': name,
                'total_rows': workbook[name].max_row
            }
            for name in workbook.sheetnames
        ]
        workbook.close()

        return jsonify({
            'rid': rid,
            'sheets': sheets,
            'active_sheet': sheets[0]['sheet_name'] if sheets else None
        })

    except Exception as e:
        logger.error(f"Error getting Excel sheets for {rid}: {str(e)}")
        return jsonify({"error": str(e)}), 500

def _resolve_file_path(source_file: str) -> Path:
    """Resolve file path from source file reference."""
    # Try direct path
    file_path = Path(source_file)
    if file_path.exists():
        return file_path

    # Try relative to repository
    repo_path = settings.get_repository_path()
    if repo_path:
        file_path = Path(repo_path) / source_file
        if file_path.exists():
            return file_path

    # Try relative to data directory
    data_dir = settings.DATA_DIR
    if data_dir:
        file_path = data_dir / source_file
        if file_path.exists():
            return file_path

    return None

def _parse_excel_file(file_path: Path, sheet_name: str = None, max_rows: int = 1000, offset: int = 0):
    """
    Parse Excel file and return structured data for the viewer.
    Supports multiple sheets, pagination, and type inference.
    """
    # Read Excel file
    excel_file = pd.ExcelFile(str(file_path))

    sheets_data = []

    # Determine which sheets to parse
    sheet_names = [sheet_name] if sheet_name and sheet_name in excel_file.sheet_names else excel_file.sheet_names

    for current_sheet in sheet_names:
        try:
            # Read sheet with pagination
            df = pd.read_excel(
                excel_file,
                sheet_name=current_sheet,
                skiprows=offset,
                nrows=max_rows
            )

            # Convert DataFrame to records
            total_rows = _get_sheet_row_count(file_path, current_sheet)

            # Clean column names
            df.columns = [str(col).strip() for col in df.columns]

            # Convert DataFrame to records with proper type handling
            # This is the CORRECT way: pandas handles all type conversions
            import json

            # Convert to JSON string then parse back - this handles ALL numpy types automatically
            records_json = df.to_json(orient='records', date_format='iso')
            records = json.loads(records_json)

            # Add row IDs for DataGrid (do this AFTER type conversion)
            for idx, record in enumerate(records):
                record['__row_id__'] = offset + idx

            # Generate column definitions
            columns = [
                {
                    'key': '__row_id__',
                    'name': '#',
                    'width': 60,
                    'resizable': False,
                    'sortable': False,
                    'filterable': False
                }
            ]

            for col in df.columns:
                # Infer column type for better rendering
                dtype = df[col].dtype
                width = _estimate_column_width(col, df[col])

                columns.append({
                    'key': col,
                    'name': col,
                    'width': width,
                    'resizable': True,
                    'sortable': True,
                    'filterable': True
                })

            # Ensure total_rows is valid (handle None from failed row count)
            total_rows = total_rows or len(records)

            sheets_data.append({
                'sheet_name': current_sheet,
                'columns': columns,
                'rows': records,
                'total_rows': total_rows,
                'has_more': offset + len(records) < total_rows
            })

        except Exception as e:
            logger.error(f"Error parsing sheet {current_sheet}: {str(e)}")
            continue

    # Check if any sheets were successfully parsed
    if not sheets_data or all(len(sheet.get('rows', [])) == 0 for sheet in sheets_data):
        error_msg = "Failed to parse Excel file. The file may contain unsupported formatting or be corrupted."
        logger.error(f"All sheets failed to parse or contain no data. Sheets attempted: {sheet_names}")
        raise Exception(error_msg)

    return {
        'sheets': sheets_data,
        'active_sheet': sheet_names[0] if sheet_names else None
    }

def _get_sheet_row_count(file_path: Path, sheet_name: str) -> int:
    """Get total row count for a sheet efficiently."""
    try:
        workbook = openpyxl.load_workbook(str(file_path), read_only=True, data_only=True)
        sheet = workbook[sheet_name]
        row_count = sheet.max_row
        workbook.close()
        return row_count
    except:
        return 0

def _estimate_column_width(column_name: str, series: pd.Series, max_width: int = 300) -> int:
    """
    Estimate appropriate column width based on content.
    Safely handles None/NaN values to prevent comparison errors.
    """
    # Base width on column name
    name_width = len(column_name) * 8 + 20

    # Sample first 100 rows for content width, filtering out None/NaN values
    sample = series.head(100)

    # Filter out None/NaN values before calculating lengths
    valid_values = sample[pd.notna(sample)]

    if len(valid_values) > 0:
        # Convert to string and calculate lengths safely
        lengths = valid_values.astype(str).str.len()
        max_content_length = int(lengths.max())  # Convert numpy int64 to Python int
        content_width = min(max_content_length * 8 + 20, max_width)
    else:
        # Column is all None/NaN - use minimal width
        content_width = 100

    # Return the larger of name width and content width, with minimum of 100px
    # Ensure return value is Python int, not numpy int64
    return int(max(name_width, content_width, 100))
