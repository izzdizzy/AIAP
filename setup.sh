#!/bin/bash

# setup.sh - Deployment Preparation Script for Hospital Readmission Predictor
# This script prepares the environment for deploying the ML application
# Run this script locally after cloning the repository

echo "============================================================"
echo "HOSPITAL READMISSION PREDICTOR - DEPLOYMENT SETUP"
echo "============================================================"
echo ""

# Exit on error
set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Step 1: Check Python version
echo "[Step 1/6] Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    print_success "Found $PYTHON_VERSION"
elif command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version)
    print_success "Found $PYTHON_VERSION"
else
    print_error "Python not found. Please install Python 3.8 or higher."
    exit 1
fi

# Step 2: Create virtual environment (recommended)
echo ""
echo "[Step 2/6] Setting up virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_success "Virtual environment created"
else
    print_warning "Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate || source venv/Scripts/activate
print_success "Virtual environment activated"

# Step 3: Upgrade pip
echo ""
echo "[Step 3/6] Upgrading pip..."
pip install --upgrade pip
print_success "Pip upgraded"

# Step 4: Install dependencies
echo ""
echo "[Step 4/6] Installing dependencies from requirements.txt..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    print_success "Dependencies installed"
else
    print_error "requirements.txt not found!"
    exit 1
fi

# Step 5: Create necessary directories
echo ""
echo "[Step 5/6] Creating necessary directories..."
mkdir -p models
mkdir -p data
mkdir -p logs
print_success "Directories created"

# Step 6: Verify installation
echo ""
echo "[Step 6/6] Verifying installation..."
python -c "import pandas; import numpy; import sklearn; import xgboost; import streamlit; import shap; import joblib" && print_success "All required packages imported successfully" || print_error "Package verification failed"

# Summary
echo ""
echo "============================================================"
echo "SETUP COMPLETE!"
echo "============================================================"
echo ""
echo "Next steps:"
echo "1. Place your training data in the 'data/' directory"
echo "2. Run 'python model.py' to train the model (update data path in model.py)"
echo "3. Run 'streamlit run app.py' to launch the application"
echo ""
echo "Important notes:"
echo "- The virtual environment is located at './venv'"
echo "- To activate it manually, run: source venv/bin/activate (Linux/Mac) or venv\\Scripts\\activate (Windows)"
echo "- Model artifacts will be saved in the 'models/' directory"
echo ""
echo "For troubleshooting, check the README.md file"
echo "============================================================"
