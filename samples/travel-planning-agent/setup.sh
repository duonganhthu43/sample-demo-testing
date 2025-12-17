#!/bin/bash

# Travel Planning Agent Setup Script

echo "Setting up Travel Planning Agent..."

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create .env from example if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "Please edit .env with your API keys"
fi

# Create output directory
mkdir -p outputs

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit .env with your API keys"
echo "  2. Activate the environment: source venv/bin/activate"
echo "  3. Run the demo: python examples/demo.py"
echo ""
