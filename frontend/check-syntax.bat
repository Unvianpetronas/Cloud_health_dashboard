@echo off
echo Checking syntax errors...

echo.
echo Checking Login.jsx...
node -c src/pages/Login.jsx
if %errorlevel% neq 0 (
    echo ERROR in Login.jsx
    pause
    exit /b 1
)

echo.
echo Checking App.js...
node -c src/App.js
if %errorlevel% neq 0 (
    echo ERROR in App.js
    pause
    exit /b 1
)

echo.
echo All syntax checks passed!
echo Starting React app...
npm start

pause