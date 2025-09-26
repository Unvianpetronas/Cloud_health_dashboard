@echo off
echo ========================================
echo   AWS Cloud Health Dashboard
echo   Professional Theme with Dark/Light Mode
echo ========================================

echo.
echo Features:
echo - Professional UI Design
echo - Dark/Light Mode Toggle
echo - AWS Color Scheme
echo - Smooth Animations
echo - Enterprise-grade Security
echo.

echo Clearing cache for fresh start...
if exist node_modules\.cache rmdir /s /q node_modules\.cache

echo.
echo Starting development server...
echo Your professional dashboard will load at http://localhost:3000
echo.
echo Toggle between Dark/Light mode using the switch in top-right corner
echo.

npm start

pause