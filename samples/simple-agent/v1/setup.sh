#!/bin/bash

# Simple Agent Setup Script
# Run this script to set up the development environment

set -e

echo "=================================="
echo "Simple Agent - Setup"
echo "=================================="
echo

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "Python version: $PYTHON_VERSION"

# Create virtual environment
echo
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo
echo "Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please edit .env and add your API keys"
fi

echo
echo "=================================="
echo "Setup Complete!"
echo "=================================="
echo
echo "Next steps:"
echo "  1. Edit .env and add your OPENAI_API_KEY"
echo "  2. Optionally add TAVILY_API_KEY for web search"
echo "  3. Run: source venv/bin/activate"
echo "  4. Run: python examples/demo.py"
echo
