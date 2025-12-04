#!/bin/bash
# Quick Test Runner for E2E Integration Tests
# Phase 6 - Quotation Pipeline

echo ""
echo "======================================================================================================"
echo "🚀 QUOTATION PIPELINE - E2E INTEGRATION TEST LAUNCHER"
echo "======================================================================================================"
echo ""

# Check Python version
echo "📌 Checking Python environment..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "✅ Activating virtual environment..."
    source venv/bin/activate
    PYTHON_CMD=python
elif command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
else
    echo "❌ Error: Python not found. Please install Python 3.7+."
    exit 1
fi

echo "✅ Using: $PYTHON_CMD ($($PYTHON_CMD --version))"
echo ""

# Check if in correct directory
if [ ! -f "tests/e2e/test_e2e_real_world.py" ]; then
    echo "❌ Error: Please run this script from the project root directory."
    echo "   Expected: /path/to/Quotation_Pipeline/"
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "   Please create .env with the following variables:"
    echo "   - ALIBABA_CLOUD_ACCESS_KEY_ID"
    echo "   - ALIBABA_CLOUD_ACCESS_KEY_SECRET"
    echo "   - DASHSCOPE_API_KEY"
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create test data directory if not exists
mkdir -p tests/data/xlsx tests/output logs

# Check if test data exists
SPECIFIC_FILE="/Users/chengpeng/Documents/MyProject/Quotation_Pipeline/tests/data/xlsx/大马彩环境资源需求（3套环境） copy.xlsx"

if [ -f "$SPECIFIC_FILE" ]; then
    echo "📝 Using specific file: $SPECIFIC_FILE"
else
    echo "❌ Error: Specific file not found: $SPECIFIC_FILE"
    echo "   Please ensure the file exists."
    exit 1
fi

# Run the test suite
echo "======================================================================================================"
echo "🏃 Running E2E Integration Tests..."
echo "======================================================================================================"
echo ""

$PYTHON_CMD tests/e2e/test_e2e_real_world.py --file "$SPECIFIC_FILE"

# Capture exit code
EXIT_CODE=$?

# Show log file location
if [ -d "logs" ]; then
    LATEST_LOG=$(ls -t logs/e2e_test_run_*.log 2>/dev/null | head -1)
    if [ ! -z "$LATEST_LOG" ]; then
        echo ""
        echo "======================================================================================================"
        echo "📋 Detailed logs saved to: $LATEST_LOG"
        echo "======================================================================================================"
    fi
fi

# Exit with test result
exit $EXIT_CODE
