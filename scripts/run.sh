#!/usr/bin/env bash
"""
Makefile equivalent for common development tasks.
Run with: ./scripts/run.sh <command>
"""

set -e

show_help() {
    echo "🚀 MFA Passport Bot Development Scripts"
    echo ""
    echo "Usage: ./scripts/run.sh <command>"
    echo ""
    echo "Available commands:"
    echo "  setup     - Set up development environment"
    echo "  dev       - Run bot in development mode with auto-reload"
    echo "  test      - Run all tests with coverage"
    echo "  lint      - Run linting and formatting"
    echo "  check     - Run all quality checks"
    echo "  clean     - Clean temporary files"
    echo "  docker    - Build and run with Docker"
    echo "  help      - Show this help message"
}

setup() {
    echo "🔧 Setting up development environment..."
    poetry install --with dev
    poetry run pre-commit install
    poetry run playwright install chromium
    echo "✅ Development environment ready!"
}

dev() {
    echo "🚀 Starting bot in development mode..."
    export DEBUG=true
    poetry run python -m bot
}

test() {
    echo "🧪 Running tests with coverage..."
    poetry run pytest --cov=bot --cov-report=term-missing --cov-report=html
}

lint() {
    echo "🔍 Running linting and formatting..."
    poetry run ruff check --fix bot/
    poetry run ruff format bot/
    poetry run black bot/
}

typecheck() {
    echo "🏷️ Running type checks..."
    poetry run mypy bot/
}

security() {
    echo "🔒 Running security checks..."
    poetry run bandit -r bot/
}

check() {
    echo "✅ Running all quality checks..."
    lint
    typecheck
    security
    test
    echo "🎉 All checks passed!"
}

clean() {
    echo "🧹 Cleaning temporary files..."
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
    rm -rf .pytest_cache .mypy_cache .coverage htmlcov logs/*.log 2>/dev/null || true
    echo "✅ Cleanup completed!"
}

docker() {
    echo "🐳 Building and running with Docker..."
    docker-compose down
    docker-compose build
    docker-compose up -d
    echo "✅ Docker containers started!"
}

# Main command dispatcher
case "${1:-help}" in
    setup) setup ;;
    dev) dev ;;
    test) test ;;
    lint) lint ;;
    typecheck) typecheck ;;
    security) security ;;
    check) check ;;
    clean) clean ;;
    docker) docker ;;
    help|*) show_help ;;
esac
