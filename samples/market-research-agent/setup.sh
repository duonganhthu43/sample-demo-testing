#!/bin/bash

# Market Research Agent - Quick Setup Script

echo "=================================="
echo "Market Research Agent - Setup"
echo "=================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $python_version"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
echo "✓ Virtual environment created"
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✓ Dependencies installed"
echo ""

# Create .env file
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✓ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file and add your API keys:"
    echo "   - OPENAI_API_KEY or ANTHROPIC_API_KEY"
    echo "   - SERPAPI_API_KEY or TAVILY_API_KEY (optional)"
    echo ""
else
    echo ".env file already exists, skipping..."
    echo ""
fi

# Create output directories
echo "Creating output directories..."
mkdir -p outputs/reports
mkdir -p outputs/traces
mkdir -p outputs/metrics
mkdir -p outputs/logs
mkdir -p outputs/visualizations
echo "✓ Output directories created"
echo ""

echo "=================================="
echo "Setup Complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your API keys"
echo "2. Run: source venv/bin/activate"
echo "3. Test: python examples/simple_example.py"
echo ""
echo "For more information, see README.md"
echo ""
