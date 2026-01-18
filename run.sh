#!/usr/bin/env bash
# Terminal File Manager Launcher Script
# Automatically sets up virtual environment and runs the application

set -e  # Exit on error

VENV_DIR=".venv"
SCRIPT_NAME="file_manager.py"
REQUIREMENTS="requirements.txt"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Print colored message
print_msg() {
    color=$1
    shift
    echo -e "${color}$@${NC}"
}

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    print_msg "$RED" "Error: Python 3 is not installed!"
    print_msg "$YELLOW" "Please install Python 3.8 or higher."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.8"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
    print_msg "$RED" "Error: Python ${PYTHON_VERSION} is too old!"
    print_msg "$YELLOW" "Please install Python ${REQUIRED_VERSION} or higher."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    print_msg "$GREEN" "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    
    print_msg "$GREEN" "Upgrading pip..."
    "$VENV_DIR/bin/python" -m pip install --upgrade pip -q
    
    if [ -f "$REQUIREMENTS" ]; then
        print_msg "$GREEN" "Installing dependencies..."
        "$VENV_DIR/bin/python" -m pip install -r "$REQUIREMENTS" -q
    fi
    
    print_msg "$GREEN" "Setup complete!"
else
    # Check if requirements have changed
    if [ -f "$REQUIREMENTS" ]; then
        print_msg "$YELLOW" "Checking dependencies..."
        "$VENV_DIR/bin/python" -m pip install -r "$REQUIREMENTS" -q --upgrade
    fi
fi

# Check if main script exists
if [ ! -f "$SCRIPT_NAME" ]; then
    print_msg "$RED" "Error: ${SCRIPT_NAME} not found!"
    exit 1
fi

# Run the application
print_msg "$GREEN" "Starting Terminal File Manager..."
echo ""
exec "$VENV_DIR/bin/python" "$SCRIPT_NAME"
