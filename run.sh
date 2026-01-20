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

PYTHON_BIN="python3"
if ! command -v "$PYTHON_BIN" &> /dev/null; then
    PYTHON_BIN="python"
fi

if ! command -v "$PYTHON_BIN" &> /dev/null; then
    print_msg "$RED" "Error: Python is not installed!"
    print_msg "$YELLOW" "Please install Python 3.8 or higher."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$($PYTHON_BIN -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.8"

if ! $PYTHON_BIN -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
    print_msg "$RED" "Error: Python ${PYTHON_VERSION} is too old!"
    print_msg "$YELLOW" "Please install Python ${REQUIRED_VERSION} or higher."
    exit 1
fi

get_venv_python() {
    if [ -x "$VENV_DIR/bin/python" ]; then
        echo "$VENV_DIR/bin/python"
        return 0
    fi
    if [ -x "$VENV_DIR/bin/python3" ]; then
        echo "$VENV_DIR/bin/python3"
        return 0
    fi
    for candidate in "$VENV_DIR"/bin/python3.*; do
        if [ -x "$candidate" ]; then
            echo "$candidate"
            return 0
        fi
    done
    return 1
}

is_venv_usable() {
    local venv_py
    venv_py=$(get_venv_python || true)
    if [ -z "$venv_py" ]; then
        return 1
    fi
    "$venv_py" -m pip --version &> /dev/null
}

handle_broken_venv() {
    print_msg "$YELLOW" "Detected an existing $VENV_DIR that is not usable on this system."
    print_msg "$YELLOW" "This often happens if $VENV_DIR was copied from another OS/device (e.g. Linux PC -> Termux)."
    print_msg "$YELLOW" "Remove $VENV_DIR and run this script again to recreate it."
    print_msg "$YELLOW" "If you want the script to recreate it automatically, run: FORCE_RECREATE_VENV=1 ./run.sh"

    if [ "${FORCE_RECREATE_VENV:-0}" != "1" ]; then
        exit 1
    fi

    backup_dir="${VENV_DIR}.broken.$(date +%Y%m%d_%H%M%S)"
    print_msg "$YELLOW" "Moving broken venv to: ${backup_dir}"
    mv "$VENV_DIR" "$backup_dir"
}

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    print_msg "$GREEN" "Creating virtual environment..."
    $PYTHON_BIN -m venv "$VENV_DIR"

    VENV_PY=$(get_venv_python || true)
    if [ -z "$VENV_PY" ]; then
        print_msg "$RED" "Error: Virtual environment Python was not created correctly."
        exit 1
    fi
    
    print_msg "$GREEN" "Upgrading pip..."
    "$VENV_PY" -m pip install --upgrade pip -q
    
    if [ -f "$REQUIREMENTS" ]; then
        print_msg "$GREEN" "Installing dependencies..."
        "$VENV_PY" -m pip install -r "$REQUIREMENTS" -q
    fi
    
    print_msg "$GREEN" "Setup complete!"
else
    if ! is_venv_usable; then
        handle_broken_venv
        print_msg "$GREEN" "Creating virtual environment..."
        $PYTHON_BIN -m venv "$VENV_DIR"
    fi

    # Check if requirements have changed
    if [ -f "$REQUIREMENTS" ]; then
        VENV_PY=$(get_venv_python || true)
        if [ -z "$VENV_PY" ]; then
            print_msg "$RED" "Error: Virtual environment Python not found. Recreate .venv."
            exit 1
        fi
        print_msg "$YELLOW" "Checking dependencies..."
        "$VENV_PY" -m pip install -r "$REQUIREMENTS" -q --upgrade
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
VENV_PY=$(get_venv_python || true)
if [ -z "$VENV_PY" ]; then
    print_msg "$RED" "Error: Virtual environment Python not found. Recreate .venv."
    exit 1
fi
exec "$VENV_PY" "$SCRIPT_NAME"
