@echo off
echo ========================================
echo   Restarting with Beautiful AWS Theme
echo ========================================

echo.
echo Clearing cache and rebuilding...
if exist node_modules\.cache rmdir /s /q node_modules\.cache
npm run build > nul 2>&1

echo.
echo Starting development server with new styles...
echo Your beautiful AWS-themed login page will load at http://localhost:3000
echo.

npm start

pause