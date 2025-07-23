#!/bin/bash
# Run script for AIRI Chatbot with virtual environment

# Get the directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if virtual environment exists
if [ ! -d "$DIR/.venv" ]; then
    echo "Error: Virtual environment not found at $DIR/.venv"
    echo "Please create it with: python3 -m venv .venv"
    exit 1
fi

# Activate virtual environment
source "$DIR/.venv/bin/activate"

# Check for required packages
echo "Checking dependencies..."
python -c "import openpyxl" 2>/dev/null || { echo "Error: openpyxl not installed"; exit 1; }
python -c "import pandas" 2>/dev/null || { echo "Error: pandas not installed"; exit 1; }
python -c "import duckdb" 2>/dev/null || { echo "Error: duckdb not installed"; exit 1; }

echo "✓ All dependencies verified"

# Run the application
echo "Starting AIRI Chatbot..."
python "$DIR/main.py" "$@"