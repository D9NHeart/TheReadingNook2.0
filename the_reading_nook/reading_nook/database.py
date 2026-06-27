import sqlite3
import hashlib
import os
import json
import shutil
from constants import DATA_DIR, BOOKS_DIR, USERS_DIR

DB_PATH = os.path.join(DATA_DIR, "nook.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        avatar_path TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        file_path TEXT NOT NULL,
        cover_path TEXT,
        total_pages INTEGER DEFAULT 0,
        added_at TEXT DEFAULT (datetime('now')),
        finished_at TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS reading_progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        current_page INTEGER DEFAULT 0,
        line_marker INTEGER DEFAULT 0,
        last_read TEXT DEFAULT (datetime('now')),
        FOREIGN KEY(book_id) REFERENCES books(id),
        FOREIGN KEY(user_id) REFERENCES users(id),
        UNIQUE(book_id, user_id)
    );

    CREATE TABLE IF NOT EXISTS bookmarks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        page INTEGER NOT NULL,
        line_y REAL DEFAULT 0,
        label TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY(book_id) REFERENCES books(id)
    );

    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        page INTEGER NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY(book_id) REFERENCES books(id)
    );

    CREATE TABLE IF NOT EXISTS stamps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        page INTEGER NOT NULL,
        stamp_type TEXT NOT NULL,
        x REAL DEFAULT 0,
        y REAL DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY(book_id) REFERENCES books(id)
    );

    CREATE TABLE IF NOT EXISTS challenges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        challenge_type TEXT NOT NULL,
        target_pages INTEGER DEFAULT 0,
        target_books INTEGER DEFAULT 0,
        period_type TEXT NOT NULL,
        start_date TEXT NOT NULL,
        end_date TEXT NOT NULL,
        completed INTEGER DEFAULT 0,
        badge_earned TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY(user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS challenge_progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        challenge_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        pages_read INTEGER DEFAULT 0,
        FOREIGN KEY(challenge_id) REFERENCES challenges(id)
    );

    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        rating INTEGER NOT NULL,
        review_text TEXT,
        dedication TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY(book_id) REFERENCES books(id),
        FOREIGN KEY(user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS user_stamps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        stamp_type TEXT NOT NULL,
        quantity INTEGER DEFAULT 1,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS stamp_trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        from_user_id INTEGER NOT NULL,
        to_user_id INTEGER NOT NULL,
        stamp_type TEXT NOT NULL,
        quantity INTEGER DEFAULT 1,
        status TEXT DEFAULT 'pending',
        created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        token TEXT NOT NULL,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY(user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS custom_stamps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        label TEXT NOT NULL,
        symbol TEXT NOT NULL,
        color TEXT NOT NULL,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY(user_id) REFERENCES users(id)
    );
    """)
    conn.commit()
    # Migration: add book_id column to challenges if not present
    try:
        conn.execute("ALTER TABLE challenges ADD COLUMN book_id INTEGER DEFAULT NULL")
        conn.commit()
    except Exception:
        pass  # Column already exists
    conn.close()


def hash_password(password: str):
    salt = os.urandom(32).hex()
    key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 200000)
    return key.hex(), salt


def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 200000)
    return key.hex() == stored_hash


def create_user(username, email, password):
    h, s = hash_password(password)
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO users (username, email, password_hash, salt) VALUES (?,?,?,?)",
            (username, email, h, s)
        )
        conn.commit()
        return True, "Account created!"
    except sqlite3.IntegrityError as e:
        if "username" in str(e):
            return False, "Username already taken."
        return False, "Email already registered."
    finally:
        conn.close()


def login_user(email, password):
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    conn.close()
    if not row:
        return None, "No account found with that email."
    if not verify_password(password, row["password_hash"], row["salt"]):
        return None, "Incorrect password."
    return dict(row), "Welcome back!"


def save_session(user_id):
    token = os.urandom(32).hex()
    conn = get_conn()
    conn.execute("DELETE FROM sessions WHERE user_id=?", (user_id,))
    conn.execute("INSERT INTO sessions (user_id, token) VALUES (?,?)", (user_id, token))
    conn.commit()
    conn.close()
    session_file = os.path.join(DATA_DIR, "session.json")
    with open(session_file, "w") as f:
        json.dump({"user_id": user_id, "token": token}, f)


def load_session():
    session_file = os.path.join(DATA_DIR, "session.json")
    if not os.path.exists(session_file):
        return None
    with open(session_file) as f:
        data = json.load(f)
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM sessions WHERE user_id=? AND token=?",
        (data["user_id"], data["token"])
    ).fetchone()
    if not row:
        conn.close()
        return None
    user = conn.execute("SELECT * FROM users WHERE id=?", (data["user_id"],)).fetchone()
    conn.close()
    return dict(user) if user else None


def clear_session():
    session_file = os.path.join(DATA_DIR, "session.json")
    if os.path.exists(session_file):
        os.remove(session_file)


def get_user_books(user_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT b.*, rp.current_page, rp.line_marker, rp.last_read "
        "FROM books b LEFT JOIN reading_progress rp ON b.id=rp.book_id AND rp.user_id=? "
        "WHERE b.user_id=? ORDER BY rp.last_read DESC NULLS LAST",
        (user_id, user_id)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_book(user_id, title, author, src_path):
    ext = os.path.splitext(src_path)[1]
    safe = "".join(c for c in title if c.isalnum() or c in " _-")[:40]
    dest_name = f"{user_id}_{safe}{ext}"
    dest = os.path.join(BOOKS_DIR, dest_name)
    shutil.copy2(src_path, dest)
    conn = get_conn()
    try:
        import fitz
        doc = fitz.open(dest)
        pages = doc.page_count
        doc.close()
    except Exception:
        pages = 0
    conn.execute(
        "INSERT INTO books (user_id, title, author, file_path, total_pages) VALUES (?,?,?,?,?)",
        (user_id, title, author, dest, pages)
    )
    conn.commit()
    book_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return book_id


def get_book(book_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM books WHERE id=?", (book_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_progress(book_id, user_id, page, line_marker=0):
    conn = get_conn()
    # Get previous page to compute delta
    prev = conn.execute(
        "SELECT current_page FROM reading_progress WHERE book_id=? AND user_id=?",
        (book_id, user_id)
    ).fetchone()
    prev_page = prev["current_page"] if prev else 0
    pages_delta = max(0, page - prev_page)

    conn.execute(
        "INSERT INTO reading_progress (book_id, user_id, current_page, line_marker) "
        "VALUES (?,?,?,?) ON CONFLICT(book_id,user_id) DO UPDATE SET "
        "current_page=excluded.current_page, line_marker=excluded.line_marker, last_read=datetime('now')",
        (book_id, user_id, page, line_marker)
    )
    conn.commit()

    # Feed pages_delta into any active challenges for this user
    if pages_delta > 0:
        today = __import__('datetime').date.today().isoformat()
        # Challenges linked to this specific book OR "all library" challenges (book_id IS NULL)
        active_challenges = conn.execute(
            "SELECT id FROM challenges WHERE user_id=? AND completed=0 "
            "AND challenge_type='pages' AND end_date >= ? "
            "AND (book_id=? OR book_id IS NULL)",
            (user_id, today, book_id)
        ).fetchall()
        for ch in active_challenges:
            conn.execute(
                "INSERT INTO challenge_progress (challenge_id, date, pages_read) VALUES (?,?,?) "
                "ON CONFLICT DO NOTHING",
                (ch["id"], today, 0)
            )
            conn.execute(
                "UPDATE challenge_progress SET pages_read=pages_read+? WHERE challenge_id=? AND date=?",
                (pages_delta, ch["id"], today)
            )
        conn.commit()
    conn.close()


def get_progress(book_id, user_id):
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM reading_progress WHERE book_id=? AND user_id=?",
        (book_id, user_id)
    ).fetchone()
    conn.close()
    return dict(row) if row else {"current_page": 0, "line_marker": 0}


def add_note(book_id, user_id, page, content):
    conn = get_conn()
    conn.execute(
        "INSERT INTO notes (book_id, user_id, page, content) VALUES (?,?,?,?)",
        (book_id, user_id, page, content)
    )
    conn.commit()
    conn.close()


def get_notes(book_id, user_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM notes WHERE book_id=? AND user_id=? ORDER BY created_at DESC",
        (book_id, user_id)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_bookmark(book_id, user_id, page, line_y, label=""):
    conn = get_conn()
    conn.execute(
        "INSERT INTO bookmarks (book_id, user_id, page, line_y, label) VALUES (?,?,?,?,?)",
        (book_id, user_id, page, line_y, label)
    )
    conn.commit()
    conn.close()


def get_bookmarks(book_id, user_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM bookmarks WHERE book_id=? AND user_id=? ORDER BY page",
        (book_id, user_id)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_bookmark(bookmark_id):
    conn = get_conn()
    conn.execute("DELETE FROM bookmarks WHERE id=?", (bookmark_id,))
    conn.commit()
    conn.close()


def add_stamp_to_page(book_id, user_id, page, stamp_type, x, y):
    conn = get_conn()
    conn.execute(
        "INSERT INTO stamps (book_id, user_id, page, stamp_type, x, y) VALUES (?,?,?,?,?,?)",
        (book_id, user_id, page, stamp_type, x, y)
    )
    conn.commit()
    conn.close()


def get_stamps_for_page(book_id, user_id, page):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM stamps WHERE book_id=? AND user_id=? AND page=?",
        (book_id, user_id, page)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_stamp(stamp_id):
    conn = get_conn()
    conn.execute("DELETE FROM stamps WHERE id=?", (stamp_id,))
    conn.commit()
    conn.close()


def create_challenge(user_id, title, challenge_type, target_pages, target_books, period_type, start_date, end_date, book_id=None):
    conn = get_conn()
    conn.execute(
        "INSERT INTO challenges (user_id,title,challenge_type,target_pages,target_books,period_type,start_date,end_date,book_id) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        (user_id, title, challenge_type, target_pages, target_books, period_type, start_date, end_date, book_id)
    )
    conn.commit()
    conn.close()


def get_challenges(user_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM challenges WHERE user_id=? ORDER BY created_at DESC",
        (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_challenge_progress(challenge_id, date_str, pages):
    conn = get_conn()
    conn.execute(
        "INSERT INTO challenge_progress (challenge_id, date, pages_read) VALUES (?,?,?) "
        "ON CONFLICT DO NOTHING",
        (challenge_id, date_str, pages)
    )
    conn.execute(
        "UPDATE challenge_progress SET pages_read=pages_read+? WHERE challenge_id=? AND date=?",
        (pages, challenge_id, date_str)
    )
    conn.commit()
    conn.close()


def get_challenge_total(challenge_id):
    conn = get_conn()
    row = conn.execute(
        "SELECT SUM(pages_read) as total FROM challenge_progress WHERE challenge_id=?",
        (challenge_id,)
    ).fetchone()
    conn.close()
    return row["total"] or 0


def add_review(book_id, user_id, rating, review_text, dedication):
    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO reviews (book_id, user_id, rating, review_text, dedication) VALUES (?,?,?,?,?)",
        (book_id, user_id, rating, review_text, dedication)
    )
    conn.execute(
        "UPDATE books SET finished_at=datetime('now') WHERE id=?",
        (book_id,)
    )
    conn.commit()
    conn.close()


def get_review(book_id, user_id):
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM reviews WHERE book_id=? AND user_id=?",
        (book_id, user_id)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def update_avatar(user_id, src_path):
    ext = os.path.splitext(src_path)[1]
    dest = os.path.join(USERS_DIR, f"avatar_{user_id}{ext}")
    shutil.copy2(src_path, dest)
    conn = get_conn()
    conn.execute("UPDATE users SET avatar_path=? WHERE id=?", (dest, user_id))
    conn.commit()
    conn.close()
    return dest


def update_user_info(user_id, username=None, email=None, password=None):
    conn = get_conn()
    if username:
        conn.execute("UPDATE users SET username=? WHERE id=?", (username, user_id))
    if email:
        conn.execute("UPDATE users SET email=? WHERE id=?", (email, user_id))
    if password:
        h, s = hash_password(password)
        conn.execute("UPDATE users SET password_hash=?, salt=? WHERE id=?", (h, s, user_id))
    conn.commit()
    conn.close()


def delete_account(user_id):
    conn = get_conn()
    conn.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.execute("DELETE FROM books WHERE user_id=?", (user_id,))
    conn.execute("DELETE FROM reading_progress WHERE user_id=?", (user_id,))
    conn.execute("DELETE FROM bookmarks WHERE user_id=?", (user_id,))
    conn.execute("DELETE FROM notes WHERE user_id=?", (user_id,))
    conn.execute("DELETE FROM stamps WHERE user_id=?", (user_id,))
    conn.execute("DELETE FROM challenges WHERE user_id=?", (user_id,))
    conn.execute("DELETE FROM reviews WHERE user_id=?", (user_id,))
    conn.execute("DELETE FROM sessions WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()
    clear_session()


def add_custom_stamp(user_id, label, symbol, color):
    import json as _json
    color_str = _json.dumps(list(color))
    conn = get_conn()
    conn.execute(
        "INSERT INTO custom_stamps (user_id, label, symbol, color) VALUES (?,?,?,?)",
        (user_id, label, symbol, color_str)
    )
    conn.commit()
    conn.close()


def get_custom_stamps(user_id):
    import json as _json
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM custom_stamps WHERE user_id=? ORDER BY created_at DESC",
        (user_id,)
    ).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        try:
            d["color"] = tuple(_json.loads(d["color"]))
        except Exception:
            d["color"] = (150, 100, 50)
        result.append(d)
    return result


def update_book_info(book_id, title, author):
    conn = get_conn()
    conn.execute(
        "UPDATE books SET title=?, author=? WHERE id=?",
        (title, author, book_id)
    )
    conn.commit()
    conn.close()


def get_most_recent_book(user_id):
    conn = get_conn()
    row = conn.execute(
        "SELECT b.*, rp.current_page, rp.line_marker FROM books b "
        "JOIN reading_progress rp ON b.id=rp.book_id AND rp.user_id=? "
        "ORDER BY rp.last_read DESC LIMIT 1",
        (user_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


