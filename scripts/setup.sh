#!/bin/bash
# AI-IN Peter — First-time Setup
set -e

echo "🃏 AI-IN Peter — Setup"
echo "======================"
echo ""

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js >= 18"
    echo "   https://nodejs.org/"
    exit 1
fi
echo "✅ Node.js $(node --version)"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python >= 3.10"
    exit 1
fi
echo "✅ Python $(python3 --version)"

# Install Node dependencies
echo ""
echo "📦 Installing Node.js dependencies..."
npm install

# Install Python dependencies
echo ""
echo "🐍 Installing Python dependencies..."
cd backend
pip3 install -r requirements.txt
cd ..

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "📝 Creating .env from template..."
    cp .env.example .env
    echo "⚠️  Edit .env to add your API keys before running!"
fi

# Create data directory for SQLite
mkdir -p backend/data

# Create assets directory for tray icon
mkdir -p assets

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit .env with your API keys"
echo "  2. Run: npm start"
echo "  3. Open your poker game in a browser"
echo "  4. Click 'Start capture' in the overlay"
echo ""
