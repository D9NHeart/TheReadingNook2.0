import pygame
import datetime
import re
from constants import *
from sprites import pixel_button, pixel_panel, make_badge_surface
from screens_auth import InputField


class ChallengesScreen:
    def __init__(self, screen, fonts, user, db):
        self.screen = screen
        self.fonts = fonts
        self.user = user
        self.db = db
        self.challenges = db.get_challenges(user["id"])
        self.my_books = db.get_user_books(user["id"]) or []
        self.show_create = False
        
        self.title_field  = InputField((SCREEN_W//2 - 180, 280, 360, 34), "Challenge Name")
        self.target_field = InputField((SCREEN_W//2 - 180, 345, 160, 34), "Target (pages/books)")
        self.end_field    = InputField((SCREEN_W//2 - 180, 410, 200, 34), "End Date (DD/MM/YYYY)")
        
        self.period_idx = 0
        self.type_idx = 0
        self.book_idx = 0
        self.msg = ""
        self.scroll = 0
        self.tick = 0

    def _parse_flexible_date(self, date_str):
        date_str = date_str.strip()
        clean = re.sub(r'[-/\s\.]+', '-', date_str)
        
        parts = clean.split('-')
        if len(parts) != 3:
            return None
            
        try:
            if len(parts[0]) == 4:
                y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
            else:
                d, m, y = int(parts[0]), int(parts[1]), int(parts[2])
                
            parsed_date = datetime.date(y, m, d)
            return parsed_date.isoformat()
        except ValueError:
            return None

    def _draw_pixel_star(self, surface, x, y):
        pixels = [
            (4, 0), (4, 1),
            (3, 2), (4, 2), (5, 2),
            (0, 3), (1, 3), (2, 3), (3, 3), (4, 3), (5, 3), (6, 3), (7, 3), (8, 3),
            (1, 4), (2, 4), (3, 4), (4, 4), (5, 4), (6, 4), (7, 4),
            (2, 5), (3, 5), (4, 5), (5, 5), (6, 5),
            (2, 6), (3, 6), (5, 6), (6, 6),
            (1, 7), (2, 7), (6, 7), (7, 7),
            (0, 8), (1, 8), (7, 8), (8, 8)
        ]
        for px, py in pixels:
            pygame.draw.rect(surface, GOLD, (x + px * 2, y + py * 2, 2, 2))

    def _draw_pixel_broken_heart(self, surface, x, y):
        left_side = [
            (1, 0), (2, 0), (0, 1), (1, 1), (2, 1), (3, 1), (0, 2), (1, 2), (2, 2), 
            (0, 3), (1, 3), (2, 3), (1, 4), (2, 4), (1, 5), (2, 5), (2, 6), (3, 7)
        ]
        right_side = [
            (5, 0), (6, 0), (5, 1), (6, 1), (7, 1), (5, 2), (6, 2), (7, 2),
            (6, 3), (7, 3), (5, 4), (6, 4), (5, 5), (4, 6), (4, 7)
        ]
        for px, py in left_side:
            pygame.draw.rect(surface, RED, (x + px * 2, y + py * 2, 2, 2))
        for px, py in right_side:
            pygame.draw.rect(surface, RED, (x + px * 2, y + py * 2, 2, 2))

    def handle_event(self, event):
        if self.show_create:
            self.title_field.handle_event(event)
            self.target_field.handle_event(event)
            self.end_field.handle_event(event)
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                period_btn = pygame.Rect(SCREEN_W//2 + 10, 345, 150, 34)
                type_btn   = pygame.Rect(SCREEN_W//2 + 10, 410, 150, 34)
                book_btn   = pygame.Rect(SCREEN_W//2 - 180, 475, 340, 34)
                save_btn   = pygame.Rect(SCREEN_W//2 - 80, 535, 160, 36)
                cancel_btn = pygame.Rect(SCREEN_W//2 - 200, 535, 100, 36)
                
                if period_btn.collidepoint(mx, my):
                    self.period_idx = (self.period_idx + 1) % 3
                if type_btn.collidepoint(mx, my):
                    self.type_idx = (self.type_idx + 1) % 2
                if book_btn.collidepoint(mx, my) and self.my_books:
                    self.book_idx = (self.book_idx + 1) % (len(self.my_books) + 1)
                if cancel_btn.collidepoint(mx, my):
                    self.show_create = False
                if save_btn.collidepoint(mx, my):
                    self._save_challenge()
            return None

        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            back_btn   = pygame.Rect(20, 20, 80, 32)
            create_btn = pygame.Rect(SCREEN_W - 180, 20, 160, 32)
            if back_btn.collidepoint(mx, my):
                return ("back",)
            if create_btn.collidepoint(mx, my):
                self.show_create = True
                self.book_idx = 0
                self.msg = ""
        if event.type == pygame.MOUSEWHEEL:
            self.scroll = max(0, self.scroll - event.y)
        return None

    def _save_challenge(self):
        title  = self.title_field.text.strip()
        target = self.target_field.text.strip()
        end_raw = self.end_field.text.strip()
        
        if not (title and target and end_raw):
            self.msg = "Please fill all fields."
            return
            
        end_iso = self._parse_flexible_date(end_raw)
        if not end_iso:
            self.msg = "Invalid date. Use DD/MM/YYYY or YYYY-MM-DD."
            return
            
        try:
            target_n = int(target)
        except ValueError:
            self.msg = "Target must be a number."
            return
            
        periods = ["daily", "monthly", "yearly"]
        types   = ["pages", "books"]
        period = periods[self.period_idx]
        ctype  = types[self.type_idx]
        start  = datetime.date.today().isoformat()
        pages  = target_n if ctype == "pages" else 0
        books  = target_n if ctype == "books" else 0
        
        associated_book_id = None
        if self.book_idx > 0 and self.my_books:
            associated_book_id = self.my_books[self.book_idx - 1]["id"]
            
        try:
            self.db.create_challenge(
                self.user["id"], title, ctype, pages, books, period, start, end_iso,
                book_id=associated_book_id
            )
        except Exception:
            pass
            
        self.challenges = self.db.get_challenges(self.user["id"])
        self.show_create = False
        self.msg = ""

    def draw(self):
        self.tick += 1
        self.screen.fill(BROWN_DARK)

        header = pygame.Surface((SCREEN_W, 64), pygame.SRCALPHA)
        header.fill((30, 18, 10, 200))
        self.screen.blit(header, (0, 0))
        pygame.draw.line(self.screen, GOLD, (0, 64), (SCREEN_W, 64), 2)

        title = self.fonts["title"].render("Reading Challenges", False, GOLD)
        self.screen.blit(title, title.get_rect(centerx=SCREEN_W//2, centery=32))

        mx, my = pygame.mouse.get_pos()
        back_btn = pygame.Rect(20, 16, 80, 32)
        pixel_button(self.screen, back_btn, "← Back", self.fonts["small"], back_btn.collidepoint(mx, my))

        create_btn = pygame.Rect(SCREEN_W - 190, 16, 170, 32)
        pixel_button(self.screen, create_btn, "+ New Challenge", self.fonts["small"], create_btn.collidepoint(mx, my))

        clip = pygame.Rect(20, 80, SCREEN_W - 40, SCREEN_H - 100)
        self.screen.set_clip(clip)
        y = 90 - self.scroll * 20

        if not self.challenges:
            empty = self.fonts["body"].render("No challenges yet — create your first one!", False, CREAM)
            self.screen.blit(empty, empty.get_rect(centerx=SCREEN_W//2, centery=SCREEN_H//2))
        else:
            for ch in self.challenges:
                card_h = 100
                card = pygame.Surface((SCREEN_W - 60, card_h), pygame.SRCALPHA)
                card.fill((40, 25, 12, 200))
                pygame.draw.rect(card, GOLD, (0, 0, card.get_width(), card_h), 2)
                self.screen.blit(card, (30, y))

                total = 0
                total = self.db.get_challenge_total(ch["id"]) or 0
                    
                target = ch["target_pages"] if ch["challenge_type"] == "pages" else ch["target_books"]
                pct = min(1.0, total / target) if target > 0 else 0

                name_s = self.fonts["body"].render(ch["title"], False, GOLD)
                self.screen.blit(name_s, (50, y + 10))

                # Show linked book name if any
                book_name = ""
                if ch.get("book_id"):
                    linked = next((b for b in self.my_books if b["id"] == ch["book_id"]), None)
                    if linked:
                        book_name = f" · 📖 {linked['title'][:18]}"

                formatted_end = ch['end_date']
                try:
                    dt = datetime.date.fromisoformat(ch['end_date'])
                    formatted_end = dt.strftime("%d/%m/%Y")
                except:
                    pass

                period_lbl = self.fonts["small"].render(
                    f"{ch['period_type'].capitalize()} · {ch['challenge_type'].capitalize()}{book_name} · ends {formatted_end}",
                    False, GOLD_LIGHT
                )
                self.screen.blit(period_lbl, (50, y + 34))

                bar_rect = pygame.Rect(50, y + 58, SCREEN_W - 160, 16)
                pygame.draw.rect(self.screen, BROWN_MID, bar_rect)
                pygame.draw.rect(self.screen, GOLD, (bar_rect.left, bar_rect.top, int(bar_rect.width * pct), bar_rect.height))
                pygame.draw.rect(self.screen, BROWN_DARK, bar_rect, 2)
                
                prog_s = self.fonts["small"].render(f"{int(total)}/{target} {ch['challenge_type']}", False, CREAM)
                self.screen.blit(prog_s, (bar_rect.right + 8, y + 59))

                is_expired = False
                try:
                    is_expired = datetime.date.today() > datetime.date.fromisoformat(ch['end_date'])
                except:
                    pass

                if pct >= 1.0:
                    badge = make_badge_surface(ch["period_type"])
                    badge = pygame.transform.scale(badge, (36, 36))
                    self.screen.blit(badge, (SCREEN_W - 80, y + 20))
                    
                    self._draw_pixel_star(self.screen, SCREEN_W - 160, y + 76)
                    done_s = self.fonts["small"].render("Complete!", False, GREEN_MID)
                    self.screen.blit(done_s, (SCREEN_W - 138, y + 76))
                elif is_expired:
                    self._draw_pixel_broken_heart(self.screen, SCREEN_W - 160, y + 76)
                    done_s = self.fonts["small"].render("Incomplete", False, RED)
                    self.screen.blit(done_s, (SCREEN_W - 138, y + 76))

                y += card_h + 14

        self.screen.set_clip(None)

        if self.show_create:
            self._draw_create_panel()

    def _draw_create_panel(self):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        panel_w, panel_h = 480, 400
        px = SCREEN_W//2 - panel_w//2
        py = 180

        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((40, 25, 12, 235))
        pygame.draw.rect(panel, GOLD, (0, 0, panel_w, panel_h), 3)
        self.screen.blit(panel, (px, py))

        hdr = self.fonts["body"].render("~ New Challenge ~", False, GOLD)
        self.screen.blit(hdr, hdr.get_rect(centerx=SCREEN_W//2, y=py + 12))

        self.title_field.draw(self.screen, self.fonts["small"])
        self.target_field.draw(self.screen, self.fonts["small"])
        self.end_field.draw(self.screen, self.fonts["small"])

        periods = ["Daily", "Monthly", "Yearly"]
        types   = ["Pages", "Books"]
        mx, my = pygame.mouse.get_pos()

        period_btn = pygame.Rect(SCREEN_W//2 + 10, 345, 150, 34)
        period_lbl_s = self.fonts["small"].render(f"Period: {periods[self.period_idx]}", False, CREAM)
        pygame.draw.rect(self.screen, BROWN_MID, period_btn)
        pygame.draw.rect(self.screen, GOLD, period_btn, 2)
        self.screen.blit(period_lbl_s, period_lbl_s.get_rect(center=period_btn.center))

        type_btn = pygame.Rect(SCREEN_W//2 + 10, 410, 150, 34)
        type_lbl_s = self.fonts["small"].render(f"Type: {types[self.type_idx]}", False, CREAM)
        pygame.draw.rect(self.screen, BROWN_MID, type_btn)
        pygame.draw.rect(self.screen, GOLD, type_btn, 2)
        self.screen.blit(type_lbl_s, type_lbl_s.get_rect(center=type_btn.center))

        book_btn = pygame.Rect(SCREEN_W//2 - 180, 475, 340, 34)
        if self.book_idx == 0 or not self.my_books:
            b_text = "Linked Book: All Library"
        else:
            b_text = f"Linked Book: {self.my_books[self.book_idx - 1]['title'][:20]}"
            
        book_lbl_s = self.fonts["small"].render(b_text, False, CREAM)
        pygame.draw.rect(self.screen, BROWN_MID, book_btn)
        pygame.draw.rect(self.screen, GOLD, book_btn, 2)
        self.screen.blit(book_lbl_s, book_lbl_s.get_rect(center=book_btn.center))

        save_btn   = pygame.Rect(SCREEN_W//2 - 80, 535, 160, 36)
        cancel_btn = pygame.Rect(SCREEN_W//2 - 210, 535, 100, 36)
        pixel_button(self.screen, save_btn, "Create!", self.fonts["small"], save_btn.collidepoint(mx, my))
        pixel_button(self.screen, cancel_btn, "Cancel", self.fonts["small"], cancel_btn.collidepoint(mx, my))

        if self.msg:
            m = self.fonts["small"].render(self.msg, False, RED)
            self.screen.blit(m, m.get_rect(centerx=SCREEN_W//2, y=580))
