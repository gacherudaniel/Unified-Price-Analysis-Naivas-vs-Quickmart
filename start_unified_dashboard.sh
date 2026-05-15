#!/bin/bash
# Launch script for Unified Price Analysis Dashboard

echo "=========================================="
echo "Unified Price Analysis Dashboard"
echo "Naivas vs Quickmart Comparison"
echo "=========================================="
echo ""

# Activate virtual environment
if [ -d "dashboard_env" ]; then
    source dashboard_env/bin/activate
    echo "✓ Virtual environment activated"
else
    echo "❌ Virtual environment not found. Run ./start_dashboard.sh first to create it."
    exit 1
fi

echo "Starting Unified Dashboard..."
echo "Access at: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop"
echo ""

streamlit run dashboard_unified.py
