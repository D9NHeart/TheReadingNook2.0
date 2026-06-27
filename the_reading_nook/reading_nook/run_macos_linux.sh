#!/bin/bash
echo "Installing The Reading Nook dependencies..."
pip3 install pygame PyMuPDF bcrypt Pillow

echo ""
echo "Starting The Reading Nook..."
python3 main.py
