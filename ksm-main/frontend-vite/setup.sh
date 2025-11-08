#!/bin/bash

# Setup Script untuk Frontend Vite
# Script untuk setup otomatis frontend-vite

echo "🚀 Setting up Frontend Vite..."

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
else
    echo "✅ Dependencies already installed"
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your configuration"
else
    echo "✅ .env file already exists"
fi

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your API configuration"
echo "2. Run 'npm run dev' to start development server"
echo "3. Open http://localhost:3004 in your browser"

