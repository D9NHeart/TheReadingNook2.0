import pygame
import os
from constants import *
from sprites import pixel_button, pixel_panel
from screens_auth import InputField


class RoomScreen:
    def __init__(self, screen, fonts, user, db):
        self.screen = screen
        self.fonts = fonts
        self.user = user
        self.db = db
        self.my_books = []
        self.selected_book = None
        self.show_shelf = False
        self.hover_book = None
        self.recent_book = None
        self.tick = 0

        self.pending_pdf_path = None
        self.show_book_dialog = False
        self.dialog_title_field  = InputField((0, 0, 340, 34), "Book Title", max_len=120)
        self.dialog_author_field = InputField((0, 0, 340, 34), "Author", max_len=120)
        self.dialog_error = ""

        self.show_edit_dialog = False
        self.edit_book = None
        self.edit_title_field  = InputField((0, 0, 340, 34), "Book Title", max_len=120)
        self.edit_author_field = InputField((0, 0, 340, 34), "Author", max_len=120)
        self.edit_error = ""

        self._load_books()

    def _load_books(self):
        if self.user:
            self.my_books = self.db.get_user_books(self.user["id"]) or []
            self.recent_book = self.db.get_most_recent_book(self.user["id"])

    def _open_add_dialog(self, path):
        self.pending_pdf_path = path
        default_title = os.path.basename(path).replace(".pdf", "").replace("_", " ")
        self.dialog_title_field.text = default_title
        self.dialog_author_field.text = ""
        self.dialog_error = ""
        self.show_book_dialog = True

    def _open_edit_dialog(self, book):
        self.edit_book = book
        self.edit_title_field.text  = book.get("title", "")
        self.edit_author_field.text = book.get("author", "")
        self.edit_error = ""
        self.show_edit_dialog = True

    def _position_dialog_fields(self):
        cx = SCREEN_W // 2
        self.dialog_title_field.rect  = pygame.Rect(cx - 170, 330, 340, 34)
        self.dialog_author_field.rect = pygame.Rect(cx - 170, 400, 340, 34)

    def _position_edit_fields(self):
        cx = SCREEN_W // 2
        self.edit_title_field.rect  = pygame.Rect(cx - 170, 330, 340, 34)
        self.edit_author_field.rect = pygame.Rect(cx - 170, 400, 340, 34)

    def handle_event(self, event):
        mx, my = pygame.mouse.get_pos()

        if self.show_edit_dialog:
            self._position_edit_fields()
            self.edit_title_field.handle_event(event)
            self.edit_author_field.handle_event(event)
            if event.type == pygame.MOUSEBUTTONDOWN:
                save_btn   = pygame.Rect(SCREEN_W//2 - 90, 455, 160, 36)
                cancel_btn = pygame.Rect(SCREEN_W//2 + 80, 455, 100, 36)
                if save_btn.collidepoint(mx, my):
                    t = self.dialog_title_field.text.strip() if False else self.edit_title_field.text.strip()
                    a = self.edit_author_field.text.strip()
                    if not t:
                        self.edit_error = "Title cannot be empty."
                    else:
                        self.db.update_book_info(self.edit_book["id"], t, a)
                        self._load_books()
                        self.show_edit_dialog = False
                        self.edit_book = None
                if cancel_btn.collidepoint(mx, my):
                    self.show_edit_dialog = False
                    self.edit_book = None
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                t = self.edit_title_field.text.strip()
                a = self.edit_author_field.text.strip()
                if not t:
                    self.edit_error = "Title cannot be empty."
                else:
                    self.db.update_book_info(self.edit_book["id"], t, a)
                    self._load_books()
                    self.show_edit_dialog = False
                    self.edit_book = None
            return None

        if self.show_book_dialog:
            self._position_dialog_fields()
            self.dialog_title_field.handle_event(event)
            self.dialog_author_field.handle_event(event)
            if event.type == pygame.MOUSEBUTTONDOWN:
                save_btn   = pygame.Rect(SCREEN_W//2 - 90, 455, 160, 36)
                cancel_btn = pygame.Rect(SCREEN_W//2 + 80, 455, 100, 36)
                if save_btn.collidepoint(mx, my):
                    return self._submit_add_dialog()
                if cancel_btn.collidepoint(mx, my):
                    self.show_book_dialog = False
                    self.pending_pdf_path = None
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                return self._submit_add_dialog()
            return None

        if self.show_shelf:
            if event.type == pygame.MOUSEBUTTONDOWN:
                close_btn = pygame.Rect(SCREEN_W - 120, 180, 90, 32)
                if close_btn.collidepoint(mx, my):
                    self.show_shelf = False
                    self.selected_book = None
                    return None

                add_btn = pygame.Rect(SCREEN_W//2 - 80, SCREEN_H - 140, 160, 36)
                if add_btn.collidepoint(mx, my):
                    return ("search_books",)

                panel_w, panel_h = 600, 460
                px = SCREEN_W//2 - panel_w//2
                py = SCREEN_H//2 - panel_h//2 + 20
                for i, book in enumerate(self.my_books):
                    bx = px + 40 + (i % 4) * 135
                    by = py + 80 + (i // 4) * 160
                    book_rect = pygame.Rect(bx, by, 90, 130)
                    if book_rect.collidepoint(mx, my):
                        if event.button == 1:
                            self.selected_book = book
                            return ("open_book", book)
                        elif event.button == 3:
                            self._open_edit_dialog(book)

            return None

        if event.type == pygame.MOUSEBUTTONDOWN:
            chal_btn = pygame.Rect(20, 20, 140, 32)
            sett_btn = pygame.Rect(SCREEN_W - 140, 20, 120, 32)
            shelf_trigger = pygame.Rect(840, 200, 440, 480)
            armchair_trigger = pygame.Rect(60, 380, 400, 340)

            if chal_btn.collidepoint(mx, my):
                return ("challenges",)
            if sett_btn.collidepoint(mx, my):
                return ("settings",)
            if shelf_trigger.collidepoint(mx, my):
                self._load_books()
                self.show_shelf = True
            if armchair_trigger.collidepoint(mx, my) and self.recent_book:
                return ("open_book", self.recent_book)

        return None

    def _submit_add_dialog(self):
        t = self.dialog_title_field.text.strip()
        a = self.dialog_author_field.text.strip() or "Unknown"
        if not t:
            self.dialog_error = "Please enter a title."
            return None
        if not self.pending_pdf_path:
            self.dialog_error = "No PDF selected."
            return None
        result = ("add_book_confirmed", self.pending_pdf_path, t, a)
        self.show_book_dialog = False
        self.pending_pdf_path = None
        self.dialog_title_field.text = ""
        self.dialog_author_field.text = ""
        return result

    def notify_pdf_path(self, path):
        self._open_add_dialog(path)

    def draw(self, bg_img=None):
        self.tick += 1

        if bg_img:
            self.screen.blit(bg_img, (0, 0))
        else:
            self.screen.fill((20, 12, 6))

        mx, my = pygame.mouse.get_pos()

        chal_btn = pygame.Rect(20, 20, 140, 32)
        pixel_button(self.screen, chal_btn, "Challenges", self.fonts["small"], chal_btn.collidepoint(mx, my))

        sett_btn = pygame.Rect(SCREEN_W - 140, 20, 120, 32)
        pixel_button(self.screen, sett_btn, "Settings", self.fonts["small"], sett_btn.collidepoint(mx, my))

        room_title = self.fonts["title"].render(f"~ {self.user.get('username', 'Reader')}'s Nook ~", False, GOLD)
        self.screen.blit(room_title, room_title.get_rect(centerx=SCREEN_W//2, y=22))

        shelf_trigger = pygame.Rect(840, 200, 440, 480)
        shelf_hover = shelf_trigger.collidepoint(mx, my) and not self.show_shelf
        if shelf_hover:
            pygame.draw.rect(self.screen, (255, 215, 0), shelf_trigger, 3, border_radius=4)

        armchair_trigger = pygame.Rect(60, 380, 400, 340)
        armchair_hover = armchair_trigger.collidepoint(mx, my) and self.recent_book and not self.show_shelf
        if armchair_hover:
            pygame.draw.rect(self.screen, (255, 215, 0), armchair_trigger, 3, border_radius=4)
        if self.recent_book and not self.show_shelf:
            cur = int(self.recent_book.get("current_page", 0) or 0)
            tot = int(self.recent_book.get("total_pages", 0) or 0)
            title_str = self.recent_book.get("title", "")[:22]
            hint_line1 = self.fonts["small"].render("Continue Reading", False, GOLD)
            hint_line2 = self.fonts["small"].render(f'"{title_str}"  p.{cur+1}/{tot}', False, CREAM)
            bw = max(hint_line1.get_width(), hint_line2.get_width()) + 20
            bh = 48
            bx = armchair_trigger.centerx - bw // 2
            by = armchair_trigger.top - 56
            badge = pygame.Surface((bw, bh), pygame.SRCALPHA)
            badge.fill((30, 18, 8, 210))
            pygame.draw.rect(badge, GOLD, (0, 0, bw, bh), 2)
            self.screen.blit(badge, (bx, by))
            self.screen.blit(hint_line1, (bx + 10, by + 6))
            self.screen.blit(hint_line2, (bx + 10, by + 26))

        if self.show_shelf:
            self._draw_shelf_panel()

        if self.show_book_dialog:
            self._draw_add_dialog()

        if self.show_edit_dialog:
            self._draw_edit_dialog()

    def _draw_shelf_panel(self):
        mx, my = pygame.mouse.get_pos()

        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        panel_w, panel_h = 600, 460
        px = SCREEN_W//2 - panel_w//2
        py = SCREEN_H//2 - panel_h//2 + 20
        panel_rect = pygame.Rect(px, py, panel_w, panel_h)
        pixel_panel(self.screen, panel_rect, (35, 22, 12))

        title = self.fonts["title"].render("~ Your Library ~", False, GOLD)
        self.screen.blit(title, title.get_rect(centerx=SCREEN_W//2, y=py + 15))
        pygame.draw.line(self.screen, GOLD, (px + 20, py + 55), (px + panel_w - 20, py + 55), 2)

        close_btn = pygame.Rect(SCREEN_W - 120, py + 15, 90, 32)
        pixel_button(self.screen, close_btn, "Close", self.fonts["small"], close_btn.collidepoint(mx, my))

        hint = self.fonts["small"].render("Left click to open  |  Right click to edit info", False, GOLD_LIGHT)
        self.screen.blit(hint, hint.get_rect(centerx=SCREEN_W//2, y=py + 58))

        self.hover_book = None
        for i, book in enumerate(self.my_books):
            bx = px + 40 + (i % 4) * 135
            by = py + 88 + (i // 4) * 160
            book_rect = pygame.Rect(bx, by, 90, 130)

            is_hover = book_rect.collidepoint(mx, my)
            if is_hover:
                self.hover_book = book

            pygame.draw.rect(self.screen, (140, 60, 60) if is_hover else (110, 50, 50), book_rect, border_radius=2)
            pygame.draw.rect(self.screen, GOLD if is_hover else BROWN_DARK, book_rect, 2, border_radius=2)
            pygame.draw.line(self.screen, BROWN_DARK, (bx, by + 10), (bx + 90, by + 10), 1)
            pygame.draw.line(self.screen, BROWN_DARK, (bx, by + 120), (bx + 90, by + 120), 1)

            t_str = book.get("title", "Unknown")[:12]
            t_surf = self.fonts["small"].render(t_str, False, CREAM)
            self.screen.blit(t_surf, t_surf.get_rect(centerx=book_rect.centerx, centery=book_rect.centery))

        if self.hover_book:
            hx, hy = mx + 15, my + 15
            info_w, info_h = 220, 85
            if hx + info_w > SCREEN_W:
                hx = mx - info_w - 15
            if hy + info_h > SCREEN_H:
                hy = my - info_h - 15
            info_rect = pygame.Rect(hx, hy, info_w, info_h)
            pygame.draw.rect(self.screen, (25, 15, 8), info_rect)
            pygame.draw.rect(self.screen, GOLD, info_rect, 1)
            b_title  = self.fonts["small"].render(self.hover_book.get("title",  "")[:24], False, GOLD)
            b_author = self.fonts["small"].render(f"by {self.hover_book.get('author','')[:24]}", False, CREAM)
            current  = int(self.hover_book.get("current_page", 0) or 0)
            total    = int(self.hover_book.get("total_pages",  0) or 0)
            b_pages  = self.fonts["small"].render(f"p.{current+1}/{total}", False, GOLD_LIGHT)
            self.screen.blit(b_title,  (hx + 8, hy + 8))
            self.screen.blit(b_author, (hx + 8, hy + 30))
            self.screen.blit(b_pages,  (hx + 8, hy + 52))

        add_btn = pygame.Rect(SCREEN_W//2 - 80, py + panel_h - 55, 160, 36)
        pixel_button(self.screen, add_btn, "+ Add Book", self.fonts["small"], add_btn.collidepoint(mx, my))

    def _draw_add_dialog(self):
        self._position_dialog_fields()
        mx, my = pygame.mouse.get_pos()

        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        self.screen.blit(overlay, (0, 0))

        panel_w, panel_h = 420, 260
        px = SCREEN_W//2 - panel_w//2
        py = 280
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((40, 25, 12, 240))
        pygame.draw.rect(panel, GOLD, (0, 0, panel_w, panel_h), 3)
        for cx, cy in [(0,0),(panel_w-8,0),(0,panel_h-8),(panel_w-8,panel_h-8)]:
            pygame.draw.rect(panel, GOLD, (cx, cy, 8, 8))
        self.screen.blit(panel, (px, py))

        hdr = self.fonts["body"].render("~ Add New Book ~", False, GOLD)
        self.screen.blit(hdr, hdr.get_rect(centerx=SCREEN_W//2, y=py + 14))
        sub = self.fonts["small"].render("Fill in the details before saving", False, GOLD_LIGHT)
        self.screen.blit(sub, sub.get_rect(centerx=SCREEN_W//2, y=py + 36))

        self.dialog_title_field.draw(self.screen, self.fonts["small"])
        self.dialog_author_field.draw(self.screen, self.fonts["small"])

        save_btn   = pygame.Rect(SCREEN_W//2 - 90, 455, 160, 36)
        cancel_btn = pygame.Rect(SCREEN_W//2 + 80, 455, 100, 36)
        pixel_button(self.screen, save_btn,   "Add to Library", self.fonts["small"], save_btn.collidepoint(mx, my))
        pixel_button(self.screen, cancel_btn, "Cancel",         self.fonts["small"], cancel_btn.collidepoint(mx, my))

        if self.dialog_error:
            err = self.fonts["small"].render(self.dialog_error, False, RED)
            self.screen.blit(err, err.get_rect(centerx=SCREEN_W//2, y=500))

    def _draw_edit_dialog(self):
        self._position_edit_fields()
        mx, my = pygame.mouse.get_pos()

        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        self.screen.blit(overlay, (0, 0))

        panel_w, panel_h = 420, 260
        px = SCREEN_W//2 - panel_w//2
        py = 280
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((40, 25, 12, 240))
        pygame.draw.rect(panel, GOLD, (0, 0, panel_w, panel_h), 3)
        for cx, cy in [(0,0),(panel_w-8,0),(0,panel_h-8),(panel_w-8,panel_h-8)]:
            pygame.draw.rect(panel, GOLD, (cx, cy, 8, 8))
        self.screen.blit(panel, (px, py))

        hdr = self.fonts["body"].render("~ Edit Book Info ~", False, GOLD)
        self.screen.blit(hdr, hdr.get_rect(centerx=SCREEN_W//2, y=py + 14))
        sub = self.fonts["small"].render("Update the title or author", False, GOLD_LIGHT)
        self.screen.blit(sub, sub.get_rect(centerx=SCREEN_W//2, y=py + 36))

        self.edit_title_field.draw(self.screen, self.fonts["small"])
        self.edit_author_field.draw(self.screen, self.fonts["small"])

        save_btn   = pygame.Rect(SCREEN_W//2 - 90, 455, 160, 36)
        cancel_btn = pygame.Rect(SCREEN_W//2 + 80, 455, 100, 36)
        pixel_button(self.screen, save_btn,   "Save Changes", self.fonts["small"], save_btn.collidepoint(mx, my))
        pixel_button(self.screen, cancel_btn, "Cancel",       self.fonts["small"], cancel_btn.collidepoint(mx, my))

        if self.edit_error:
            err = self.fonts["small"].render(self.edit_error, False, RED)
            self.screen.blit(err, err.get_rect(centerx=SCREEN_W//2, y=500))