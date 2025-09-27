@echo off
echo ========================================
echo   Installing and Running React App
echo ========================================

echo Current directory: %CD%
echo.

echo Checking if package.json exists...
if not exist package.json (
    echo ERROR: package.json not found!
    echo Make sure you're in the frontend directory
    pause
    exit /b 1
)

echo Found package.json, proceeding with installation...
echo.

echo Installing dependencies...
npm install

if %errorlevel% neq 0 (
    echo.
    echo ERROR: npm install failed!
    echo Trying to fix...
    npm cache clean --force
    npm install
)

echo.
echo Starting development server...
npm start

pause