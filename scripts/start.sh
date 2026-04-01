#!/bin/bash
# AI-IN Peter — Launch Script
set -e

echo "🃏 AI-IN Peter — Starting..."
echo ""

# Check .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Run: cp .env.example .env"
    echo "   Then add your API keys."
    exit 1
fi

# Start backend and frontend concurrently
npm start
