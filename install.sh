#!/bin/bash

echo "========================================="
echo "         Seedling Installer"
echo "========================================="

if ! command -v python3 &> /dev/null; then
    echo "[ERROR] python3 is not installed. Please install it first."
    exit 1
fi

echo "[1/3] Checking for pipx..."
if ! command -v pipx &> /dev/null; then
    echo "      pipx not found. Trying to install/locate it..."
    python3 -m pip install --user pipx >/dev/null 2>&1
    python3 -m pipx ensurepath >/dev/null 2>&1
    export PATH="$PATH:$HOME/.local/bin"
fi

if ! command -v pipx &> /dev/null; then
    echo "[ERROR] pipx is required but not found."
    echo "        Please install it manually: 'brew install pipx' (Mac) or 'sudo apt install pipx' (Linux)"
    exit 1
fi

echo "[2/3] Installing TreeWeaver commands ('scan' & 'build')..."
pipx install . --force

echo "[3/3] Finalizing installation..."
pipx ensurepath >/dev/null 2>&1

echo "========================================="
echo "   Installation successful!"
echo "   - Type 'scan' to explore directories."
echo "   - Type 'build' to construct structures."
echo "========================================="
echo "💡 Note: Please restart your terminal if 'scan' is not found."

exit 0