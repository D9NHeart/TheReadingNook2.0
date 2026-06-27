import pygame
import sys
import os

from constants import *
import database as db_module

STATE_LOGIN      = "login"
STATE_REGISTER   = "register"
STATE_ROOM       = "room"
STATE_READER     = "reader"
STATE_CHALLENGES = "challenges"
STATE_SETTINGS   = "settings"


def load_fonts():
    font_path = os.path.join(FONTS_DIR, "pixel.ttf")
    sizes = {"title": 28, "body": 18, "small": 14}
    fonts = {}
    for name, size in sizes.items():
        if os.path.exists(font_path):
            try:
                fonts[name] = pygame.font.Font(font_path, size)
                continue
            except Exception:
                pass
        fonts[name] = pygame.font.SysFont("courier", size, bold=(name == "title"))
    return fonts


def open_file_dialog(filetypes="pdf"):
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        if filetypes == "pdf":
            path = filedialog.askopenfilename(
                title="Select a PDF file",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
            )
        else:
            path = filedialog.askopenfilename(
                title="Select a profile picture",
                filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.gif"),
                           ("All files", "*.*")]
            )
        root.destroy()
        return path if path else None
    except Exception as e:
        print(f"File dialog error: {e}")
        return None


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    db_module.init_db()
    fonts = load_fonts()

    bg_login = None
    bg_room  = None
    try:
        bg_login = pygame.image.load(os.path.join(IMAGES_DIR, "main_bg.png"))
        bg_login = pygame.transform.scale(bg_login, (SCREEN_W, SCREEN_H))
        bg_room  = pygame.image.load(os.path.join(IMAGES_DIR, "room_bg.png"))
        bg_room  = pygame.transform.scale(bg_room, (SCREEN_W, SCREEN_H))
    except Exception as e:
        print(f"Could not load background: {e}")

    current_user = db_module.load_session()
    state = STATE_ROOM if current_user else STATE_LOGIN

    from screens_auth import LoginScreen, RegisterScreen
    from screens_room import RoomScreen
    from screens_reader import ReaderScreen
    from screens_challenges import ChallengesScreen
    from screens_settings import SettingsScreen

    login_screen     = LoginScreen(screen, fonts, bg_login)
    register_screen  = RegisterScreen(screen, fonts, bg_login)
    room_screen      = None
    reader_screen    = None
    challenge_screen = None
    settings_screen  = None

    def enter_room():
        nonlocal room_screen
        room_screen = RoomScreen(screen, fonts, current_user, db_module)

    if current_user:
        enter_room()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif state == STATE_LOGIN:
                result = login_screen.handle_event(event)
                if result:
                    action = result[0]
                    if action == "login":
                        _, email, password, stay = result
                        if not email or not password:
                            login_screen.error = "Please fill in all fields."
                        else:
                            user, msg = db_module.login_user(email, password)
                            if user:
                                current_user = user
                                if stay:
                                    db_module.save_session(user["id"])
                                enter_room()
                                state = STATE_ROOM
                                login_screen.error = ""
                            else:
                                login_screen.error = msg
                elif login_screen.mode == "register":
                    state = STATE_REGISTER
                    login_screen.mode = "login"

            elif state == STATE_REGISTER:
                result = register_screen.handle_event(event)
                if result:
                    action = result[0]
                    if action == "register":
                        _, username, email, pw, pw2 = result
                        if not all([username, email, pw, pw2]):
                            register_screen.error = "Please fill all fields."
                        elif pw != pw2:
                            register_screen.error = "Passwords do not match."
                        elif len(pw) < 6:
                            register_screen.error = "Password must be at least 6 chars."
                        else:
                            ok, msg = db_module.create_user(username, email, pw)
                            if ok:
                                state = STATE_LOGIN
                                login_screen.error = "Account created! Please log in."
                                register_screen = RegisterScreen(screen, fonts, bg_login)
                            else:
                                register_screen.error = msg
                    elif action == "back":
                        state = STATE_LOGIN

            elif state == STATE_ROOM:
                if room_screen:
                    result = room_screen.handle_event(event)
                    if result:
                        action = result[0]
                        if action == "search_books":
                            pygame.event.pump()
                            path = open_file_dialog("pdf")
                            if path and room_screen:
                                room_screen.notify_pdf_path(path)
                        elif action == "add_book_confirmed":
                            _, pdf_path, b_title, b_author = result
                            try:
                                db_module.add_book(current_user["id"], b_title, b_author, pdf_path)
                                room_screen._load_books()
                            except Exception as e:
                                print(e)
                        elif action == "open_book":
                            book = dict(result[1])
                            reader_screen = ReaderScreen(screen, fonts, book, current_user, db_module)
                            state = STATE_READER
                        elif action == "challenges":
                            challenge_screen = ChallengesScreen(screen, fonts, current_user, db_module)
                            state = STATE_CHALLENGES
                        elif action == "settings":
                            settings_screen = SettingsScreen(screen, fonts, current_user, db_module)
                            state = STATE_SETTINGS

            elif state == STATE_READER:
                if reader_screen:
                    result = reader_screen.handle_event(event)
                    if result:
                        action = result[0]
                        if action == "back":
                            enter_room()
                            state = STATE_ROOM

            elif state == STATE_CHALLENGES:
                if challenge_screen:
                    result = challenge_screen.handle_event(event)
                    if result and result[0] == "back":
                        state = STATE_ROOM

            elif state == STATE_SETTINGS:
                if settings_screen:
                    result = settings_screen.handle_event(event)
                    if result:
                        action = result[0]
                        if action == "back":
                            state = STATE_ROOM
                            enter_room()
                        elif action == "logout":
                            db_module.clear_session()
                            current_user = None
                            login_screen = LoginScreen(screen, fonts, bg_login)
                            state = STATE_LOGIN
                        elif action == "delete_account":
                            db_module.delete_account(current_user["id"])
                            current_user = None
                            login_screen = LoginScreen(screen, fonts, bg_login)
                            state = STATE_LOGIN
                        elif action == "pick_avatar":
                            pygame.event.pump()
                            path = open_file_dialog("image")
                            if path and settings_screen:
                                settings_screen.set_avatar(path)

        if state == STATE_LOGIN:
            login_screen.draw()
        elif state == STATE_REGISTER:
            register_screen.draw()
        elif state == STATE_ROOM and room_screen:
            room_screen.draw(bg_room)
        elif state == STATE_READER and reader_screen:
            reader_screen.draw()
        elif state == STATE_CHALLENGES and challenge_screen:
            challenge_screen.draw()
        elif state == STATE_SETTINGS and settings_screen:
            settings_screen.draw()

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()