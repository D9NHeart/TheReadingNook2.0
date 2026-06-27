@echo off
echo Installing The Reading Nook dependencies...
pip install pygame PyMuPDF bcrypt Pillow
echo.
echo Starting The Reading Nook...
python main.py
pause
