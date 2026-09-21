@echo off
title AI Air Canvas - Virtual Painter
echo ===================================================
echo       Launching AI Air Canvas - Virtual Painter
echo ===================================================
echo.

python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Error installing dependencies!
    pause
    exit /b %errorlevel%
)

echo.
echo Starting application...
python virtual_painter.py

if %errorlevel% neq 0 (
    echo.
    echo Application exited with an error.
    pause
)
