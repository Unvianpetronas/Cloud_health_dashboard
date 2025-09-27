@echo off
echo ========================================
echo   Testing React App After Fix
echo ========================================

echo Backing up current App.js...
if exist src\App-backup.js del src\App-backup.js
copy src\App.js src\App-backup.js

echo Using test version...
copy src\App-test.js src\App.js

echo Starting React development server...
echo If this works, the error is fixed!
echo Press Ctrl+C to stop and restore original App.js
echo.

npm start

echo.
echo Restoring original App.js...
copy src\App-backup.js src\App.js
del src\App-backup.js

pause