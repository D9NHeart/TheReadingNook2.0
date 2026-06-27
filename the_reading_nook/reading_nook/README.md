# The Reading Nook

A cozy pixel-art gamified PDF reader, built with Python & Pygame.

---

## Setup

### Requirements
- Python 3.8+
- pip

### Install & Run

**Windows:**
```
Double-click run_windows.bat
```
Or manually:
```
pip install pygame PyMuPDF bcrypt Pillow
python main.py
```

**macOS / Linux:**
```
chmod +x run_macos_linux.sh
./run_macos_linux.sh
```
Or manually:
```
pip3 install pygame PyMuPDF bcrypt Pillow
python3 main.py
```

---

## Features

###  Library
- Upload PDFs using a native file picker (no path copying needed)
- Each book stores title and author
- Books are saved locally and work offline

### PDF Reader
- Warm pixelart frame around the PDF
- **Pen** — write notes (up to 2700 chars) on any page
- **Bookmark/Marker** — click to place a red line marker exactly where you stopped
- **Notepad** — review all your saved notes with dates
- **Stamps** — place pixelart stamps from famous books: Hobbit, ASOIAF, Peter Rabbit, Alice in Wonderland, Narnia, Harry Potter, The Little Prince
- Navigate with arrow keys, scroll wheel, or on-screen buttons
- Auto-saves progress when you close the book

###  Challenges
- Set reading challenges: X pages or books by a chosen date
- Daily, monthly, or yearly period types
- Earn pixel badges when you complete a challenge

###  Reviews
- At the end of a book, leave a star rating (1–5) and review text
- Dedicate the book to someone
- Inspired by Letterboxd

###  Accounts
- Email + password login with bcrypt hashing + salt
- "Stay logged in" session option
- Set a profile picture (optional, editable in Settings)
- Change username, email, or password anytime
- Delete account with double confirmation

---

## File locations
- Books stored in: `data/books/`
- User data stored in: `data/nook.db`
- Profile pictures in: `data/users/`

---

## Fonts
Place a pixel font TTF named `pixel.ttf` inside `assets/fonts/` for the full pixelart look.
Recommended free fonts: Press Start 2P, Silkscreen, or Pixel Operator.
Download from Google Fonts or dafont.com — the game falls back to Courier if none is found.
