@echo off
REM Setup Script untuk Frontend Vite (Windows)
REM Script untuk setup otomatis frontend-vite

echo 🚀 Setting up Frontend Vite...

REM Check if node_modules exists
if not exist "node_modules" (
    echo 📦 Installing dependencies...
    call npm install
) else (
    echo ✅ Dependencies already installed
)

REM Check if .env exists
if not exist ".env" (
    echo 📝 Creating .env file from .env.example...
    copy .env.example .env
    echo ⚠️  Please edit .env file with your configuration
) else (
    echo ✅ .env file already exists
)

echo ✅ Setup complete!
echo.
echo Next steps:
echo 1. Edit .env file with your API configuration
echo 2. Run 'npm run dev' to start development server
echo 3. Open http://localhost:3004 in your browser

pause

