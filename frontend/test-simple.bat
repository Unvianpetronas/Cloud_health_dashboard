@echo off
echo Backing up original App.js...
copy src\App.js src\App-original.js

echo Using simple App.js for testing...
copy src\App-simple.js src\App.js

echo Starting React development server...
npm start

echo Restoring original App.js...
copy src\App-original.js src\App.js
del src\App-original.js

pause