#!/bin/bash

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

info() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} ✅ $1"; }
warning() { echo -e "${YELLOW}[WARNING]${NC} ⚠️  $1"; }
error() { echo -e "${RED}[ERROR]${NC} ❌ $1"; }
header() {
    echo -e "\n${CYAN}========================================"
    echo -e "  $1"
    echo -e "========================================${NC}"
}


header "Running pre-commit check"

header "STEP 1: Linting"

if docker compose run --rm backend flake8 --config=app/.flake8 app/; then
    success "No linting issues found."
else
    warning "Linting issues detected! Please fix them."
fi

header "STEP 2: Test"

if docker compose run --rm -e PYTHONPATH=/app -w /app/app backend pytest test/ -vv; then
    success "All tests passed!"
else
    error "Some tests failed!"
    exit 1
fi

header "Pre commit check finished"