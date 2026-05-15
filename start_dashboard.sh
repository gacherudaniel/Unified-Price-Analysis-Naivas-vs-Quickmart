#!/bin/bash
# Quick Start Script for Retail Price Analytics Dashboard

echo "=========================================="
echo "Retail Price Analytics Dashboard"
echo "=========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "dashboard_env" ]; then
    echo "Creating virtual environment..."
    python3 -m venv dashboard_env
    
    echo "Activating virtual environment..."
    source dashboard_env/bin/activate
    
    echo "Installing dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    
    echo "✓ Setup complete!"
    echo ""
else
    echo "✓ Virtual environment found"
    source dashboard_env/bin/activate
fi

echo "Starting Streamlit dashboard..."
echo "The dashboard will open in your browser automatically."
echo ""
echo "To stop the dashboard, press Ctrl+C"
echo ""

streamlit run dashboard.py
