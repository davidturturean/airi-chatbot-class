#!/bin/bash

# Auto-sync script for airi-chatbot-class
# Usage: ./auto-sync.sh [branch-name]

BRANCH=${1:-main}
WATCH_DIR="/Users/davidturturean/Documents/Codingprojects/airi-chatbot-class"

echo "Starting auto-sync for branch: $BRANCH"
echo "Watching directory: $WATCH_DIR"

# Function to sync changes
sync_changes() {
    cd "$WATCH_DIR"
    
    # Check if there are changes
    if [[ -n $(git status --porcelain) ]]; then
        echo "Changes detected, syncing..."
        
        # Add all changes
        git add .
        
        # Commit with timestamp
        git commit -m "Auto-sync: $(date '+%Y-%m-%d %H:%M:%S')"
        
        # Push to specified branch
        git push origin "$BRANCH"
        
        echo "Sync completed at $(date)"
    fi
}

# Check if fswatch is available
if ! command -v fswatch &> /dev/null; then
    echo "fswatch not found. Please install it first:"
    echo "brew install fswatch"
    exit 1
fi

# Watch for file changes and sync
echo "Monitoring for changes... Press Ctrl+C to stop."
fswatch -o "$WATCH_DIR" --exclude="\.git" --exclude="\.venv" --exclude="node_modules" --exclude="__pycache__" | while read f; do
    sync_changes
done