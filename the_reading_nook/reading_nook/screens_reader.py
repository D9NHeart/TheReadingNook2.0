import pygame
import os
import math
from constants import *
from sprites import (draw_page_frame, draw_warm_overlay, make_stamp_surface,
                     pixel_button, pixel_panel, STAMP_DATA, draw_star_rating)
from screens_auth import InputField


TOOL_PEN        = "pen"
TOOL_BOOKMARK   = "bookmark"
TOOL_NOTEPAD    = "notepad"
TOOL_STAMPS     = "stamps"
TOOL_NONE       = "none"

CUSTOM_STAMP_COLORS = [
    (180, 60,  60),
    (60,  120, 180),
    (60,  160, 80),
    (160, 100, 40),
    (120, 60,  160),
    (180, 140, 40),
    (60,  160, 160),
    (180, 80,  140),
]


class ReaderScreen:
    def __init__(self, screen, fonts, book, user, db):
        self.screen = screen
        self.fonts = fonts
        self.book = dict(book) if book else {}
        self.user = user
        self.db = db

        self.doc = None
        
        t_pages = self.book.get("total_pages", 0)
        c_pages = self.book.get("current_page", 0)
        self.total_pages = int(t_pages) if t_pages is not None else 0
        self.current_page = int(c_pages) if c_pages is not None else 0
        
        l_marker = self.book.get("line_marker", 0)
        self.line_marker_y = float(l_marker) if l_marker is not None else 0.0
        self.page_surf = None

        self.active_tool = TOOL_NONE
        self.note_text = ""
        self.note_field = InputField((0, 0, 420, 28), max_len=2700)
        self.note_active = False

        self.bookmarks = []
        self.notes = []
        self.stamps_on_page = []
        self.selected_stamp = None

        self.show_review = False
        self.review_rating = 0
        self.review_text_field = InputField((0, 0, 400, 120), max_len=2000)
        self.review_text_field.rect = pygame.Rect(SCREEN_W//2 - 200, 350, 400, 120)
        self.dedication_field = InputField((0, 0, 400, 34), max_len=200)
        self.dedication_field.rect = pygame.Rect(SCREEN_W//2 - 200, 500, 400, 34)
        self.review_msg = ""
        self.review_hover_star = -1

        self.page_rect = pygame.Rect(80, 60, SCREEN_W - 200, SCREEN_H - 80)
        self.toolbar_rect = pygame.Rect(SCREEN_W - 108, 60, 96, SCREEN_H - 80)

        self.dragging_marker = False
        self.note_scroll = 0
        self.tick = 0

        self.show_edit_book = False
        self.edit_title_field  = InputField((SCREEN_W//2 - 170, 320, 340, 34), "Book Title", max_len=120)
        self.edit_author_field = InputField((SCREEN_W//2 - 170, 385, 340, 34), "Author",     max_len=120)
        self.edit_book_msg = ""

        self.show_custom_stamp = False
        self.custom_stamp_label = InputField((0, 0, 200, 30), "Label (12 chars)", max_len=12)
        self.custom_stamp_symbol = InputField((0, 0, 60, 30), "Symbol (1-2 chars)", max_len=2)
        self.custom_stamp_color_idx = 0
        self.custom_stamp_msg = ""
        self.custom_stamps = []
        self._load_custom_stamps()

        self._load_doc()
        self._load_page_data()

    def _load_custom_stamps(self):
        try:
            self.custom_stamps = self.db.get_custom_stamps(self.user["id"])
        except Exception:
            self.custom_stamps = []

    def _load_doc(self):
        try:
            import fitz
            path = self.book.get("file_path", "")
            if os.path.exists(path):
                self.doc = fitz.open(path)
                self.total_pages = int(self.doc.page_count)
                self._render_page()
        except Exception as e:
            self.doc = None

    def _render_page(self):
        if not self.doc:
            return
        try:
            import fitz
            page = self.doc[self.current_page]
            mat = fitz.Matrix(1.4, 1.4)
            pix = page.get_pixmap(matrix=mat)
            
            surf = self._pix_to_surf(pix)
            
            if isinstance(self.page_rect, pygame.Rect):
                pr_w, pr_h = self.page_rect.width, self.page_rect.height
            else:
                pr_w, pr_h = self.page_rect[2], self.page_rect[3]

            target_w = pr_w - 40
            target_h = pr_h - 40
            ratio = min(target_w / surf.get_width(), target_h / surf.get_height())
            nw = int(surf.get_width() * ratio)
            nh = int(surf.get_height() * ratio)
            self.page_surf = pygame.transform.scale(surf, (nw, nh))
        except Exception as e:
            self.page_surf = None

    def _pix_to_surf(self, pix):
        import fitz
        # Always convert to RGB to avoid mode mismatches (grayscale, CMYK, etc.)
        if pix.colorspace and pix.colorspace != fitz.csRGB:
            pix = fitz.Pixmap(fitz.csRGB, pix)
        raw = pix.samples
        mode = "RGBA" if pix.n == 4 else "RGB"
        surf = pygame.image.fromstring(raw, (pix.width, pix.height), mode)
        return surf

    def _load_page_data(self):
        if not self.book.get("id") or not self.user.get("id"):
            return
        book_id = self.book["id"]
        user_id = self.user["id"]
        self.bookmarks = self.db.get_bookmarks(book_id, user_id) or []
        self.notes = self.db.get_notes(book_id, user_id) or []
        self.stamps_on_page = self.db.get_stamps_for_page(book_id, user_id, self.current_page) or []

    def _save_progress(self):
        if not self.book.get("id") or not self.user.get("id"):
            return
        self.book["current_page"] = int(self.current_page)
        self.book["total_pages"] = int(self.total_pages)
        
        if isinstance(self.page_rect, pygame.Rect):
            pr_h = self.page_rect.height
        else:
            pr_h = self.page_rect[3]

        self.db.update_progress(
            self.book["id"], self.user["id"],
            int(self.current_page), int(self.line_marker_y * pr_h)
        )

    def _go_to_page(self, p):
        if self.total_pages <= 0:
            return
        self.current_page = max(0, min(int(p), self.total_pages - 1))
        self._render_page()
        self._load_page_data()
        self._save_progress()
        if self.current_page == self.total_pages - 1:
            self.show_review = True

    def handle_event(self, event):
        if self.show_review:
            return self._handle_review_event(event)

        if self.show_edit_book:
            return self._handle_edit_book_event(event)

        if self.show_custom_stamp:
            return self._handle_custom_stamp_event(event)

        if self.active_tool == TOOL_PEN:
            self.note_field.handle_event(event)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.active_tool = TOOL_NONE
                return None
            if event.key == pygame.K_RIGHT or event.key == pygame.K_PAGEDOWN:
                self._go_to_page(self.current_page + 1)
            if event.key == pygame.K_LEFT or event.key == pygame.K_PAGEUP:
                self._go_to_page(self.current_page - 1)

        if event.type == pygame.MOUSEWHEEL:
            if self.active_tool == TOOL_NOTEPAD:
                self.note_scroll = max(0, self.note_scroll - event.y * 2)
            else:
                self._go_to_page(self.current_page + (1 if event.y < 0 else -1))

        if isinstance(self.page_rect, pygame.Rect):
            pr_left, pr_top = self.page_rect.left, self.page_rect.top
            pr_width, pr_height = self.page_rect.width, self.page_rect.height
            is_collide = self.page_rect.collidepoint
        else:
            pr_left, pr_top, pr_width, pr_height = self.page_rect[0], self.page_rect[1], self.page_rect[2], self.page_rect[3]
            is_collide = pygame.Rect(pr_left, pr_top, pr_width, pr_height).collidepoint

        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            result = self._handle_toolbar_click(mx, my)
            if result:
                return result

            if self.active_tool == TOOL_STAMPS and event.button == 3:
                for stamp in self.stamps_on_page:
                    sx = int(pr_left + stamp["x"] * pr_width)
                    sy = int(pr_top  + stamp["y"] * pr_height)
                    dist = math.hypot(mx - sx, my - sy)
                    if dist < 24:
                        self.db.delete_stamp(stamp["id"])
                        self._load_page_data()
                        return None

            if self.active_tool == TOOL_BOOKMARK:
                if is_collide(mx, my):
                    rel_y = (my - pr_top) / pr_height
                    self.line_marker_y = float(rel_y)
                    self.db.add_bookmark(
                        self.book["id"], self.user["id"],
                        self.current_page, rel_y, f"p.{self.current_page+1}"
                    )
                    self._save_progress()
                    self._load_page_data()
                    self.active_tool = TOOL_NONE

            elif self.active_tool == TOOL_STAMPS and self.selected_stamp and event.button == 1:
                if is_collide(mx, my):
                    rx = (mx - pr_left) / pr_width
                    ry = (my - pr_top)  / pr_height
                    self.db.add_stamp_to_page(
                        self.book["id"], self.user["id"],
                        self.current_page, self.selected_stamp, rx, ry
                    )
                    self._load_page_data()

            elif self.active_tool == TOOL_STAMPS and event.button == 1:
                new_stamp_btn = getattr(self, "_stamp_new_btn_rect", None)
                if new_stamp_btn and new_stamp_btn.collidepoint(mx, my):
                    self.custom_stamp_label.text  = ""
                    self.custom_stamp_symbol.text = ""
                    self.custom_stamp_color_idx   = 0
                    self.custom_stamp_msg = ""
                    self.show_custom_stamp = True
                    return None
                all_list = getattr(self, "_all_stamps_list_cache", list(STAMP_DATA.items()))
                for i, (stype, _) in enumerate(all_list):
                    sr = self._stamp_selector_rect_by_index(i)
                    if sr.collidepoint(mx, my):
                        self.selected_stamp = stype

            elif self.active_tool == TOOL_PEN:
                save_btn = pygame.Rect(pr_left + 10, pr_top + pr_height - 50, 100, 32)
                if save_btn.collidepoint(mx, my) and self.note_field.text.strip():
                    self.db.add_note(
                        self.book["id"], self.user["id"],
                        self.current_page, self.note_field.text.strip()
                    )
                    self.note_field.text = ""
                    self.active_tool = TOOL_NONE
                    self._load_page_data()

            back_btn = pygame.Rect(10, SCREEN_H - 44, 80, 34)
            prev_btn = pygame.Rect(10, SCREEN_H//2 - 24, 44, 48)
            next_btn = pygame.Rect(SCREEN_W - 168, SCREEN_H//2 - 24, 44, 48)
            if back_btn.collidepoint(mx, my):
                self._save_progress()
                return ("back",)
            if prev_btn.collidepoint(mx, my):
                self._go_to_page(self.current_page - 1)
            if next_btn.collidepoint(mx, my):
                self._go_to_page(self.current_page + 1)
            edit_rect = getattr(self, "_edit_info_btn_rect", None)
            if edit_rect and edit_rect.collidepoint(mx, my):
                self.edit_title_field.text  = self.book.get("title", "")
                self.edit_author_field.text = self.book.get("author", "")
                self.edit_book_msg = ""
                self.show_edit_book = True

        return None

    def _handle_edit_book_event(self, event):
        py = 280
        self.edit_title_field.rect  = pygame.Rect(SCREEN_W//2 - 170, py + 60, 340, 34)
        self.edit_author_field.rect = pygame.Rect(SCREEN_W//2 - 170, py + 125, 340, 34)
        self.edit_title_field.handle_event(event)
        self.edit_author_field.handle_event(event)
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            save_btn   = pygame.Rect(SCREEN_W//2 - 90, py + 185, 160, 36)
            cancel_btn = pygame.Rect(SCREEN_W//2 + 80, py + 185, 100, 36)
            if save_btn.collidepoint(mx, my):
                t = self.edit_title_field.text.strip()
                a = self.edit_author_field.text.strip() or "Unknown"
                if not t:
                    self.edit_book_msg = "Title cannot be empty."
                else:
                    self.db.update_book_info(self.book["id"], t, a)
                    self.book["title"] = t
                    self.book["author"] = a
                    self.edit_book_msg = "Saved!"
                    self.show_edit_book = False
            if cancel_btn.collidepoint(mx, my):
                self.show_edit_book = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.show_edit_book = False
        return None

    def _handle_custom_stamp_event(self, event):
        py = 280
        cx = SCREEN_W // 2
        self.custom_stamp_label.rect  = pygame.Rect(cx - 110, py + 60, 200, 30)
        self.custom_stamp_symbol.rect = pygame.Rect(cx + 100, py + 60, 60, 30)
        self.custom_stamp_label.handle_event(event)
        self.custom_stamp_symbol.handle_event(event)
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            for i, col in enumerate(CUSTOM_STAMP_COLORS):
                cr = pygame.Rect(cx - 110 + i * 36, py + 118, 28, 28)
                if cr.collidepoint(mx, my):
                    self.custom_stamp_color_idx = i
            save_btn   = pygame.Rect(cx - 90, py + 200, 160, 34)
            cancel_btn = pygame.Rect(cx + 80, py + 200, 90, 34)
            if save_btn.collidepoint(mx, my):
                label  = self.custom_stamp_label.text.strip()[:12]
                symbol = self.custom_stamp_symbol.text.strip()[:2] or "?"
                color  = CUSTOM_STAMP_COLORS[self.custom_stamp_color_idx]
                if not label:
                    self.custom_stamp_msg = "Enter a label."
                else:
                    try:
                        self.db.add_custom_stamp(self.user["id"], label, symbol, color)
                        self._load_custom_stamps()
                        self.custom_stamp_msg = ""
                        self.show_custom_stamp = False
                    except Exception as e:
                        self.custom_stamp_msg = str(e)
            if cancel_btn.collidepoint(mx, my):
                self.show_custom_stamp = False
                self.custom_stamp_msg = ""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.show_custom_stamp = False
        return None

    def _handle_toolbar_click(self, mx, my):
        tools = [TOOL_PEN, TOOL_BOOKMARK, TOOL_NOTEPAD, TOOL_STAMPS]
        for i, tool in enumerate(tools):
            tr = self._tool_rect(i)
            if tr.collidepoint(mx, my):
                self.active_tool = tool if self.active_tool != tool else TOOL_NONE
                if tool == TOOL_PEN:
                    if isinstance(self.page_rect, pygame.Rect):
                        pr_left, pr_top, pr_width, pr_height = self.page_rect.left, self.page_rect.top, self.page_rect.width, self.page_rect.height
                    else:
                        pr_left, pr_top, pr_width, pr_height = self.page_rect[0], self.page_rect[1], self.page_rect[2], self.page_rect[3]
                    
                    self.note_field.text = ""
                    self.note_field.active = True
                    self.note_field.rect = pygame.Rect(
                        pr_left + 10,
                        pr_top + pr_height - 170,
                        pr_width - 20, 110
                    )
                return None
        return None

    def _tool_rect(self, index):
        if isinstance(self.toolbar_rect, pygame.Rect):
            tb_left, tb_top = self.toolbar_rect.left, self.toolbar_rect.top
        else:
            tb_left, tb_top = self.toolbar_rect[0], self.toolbar_rect[1]
        bw, bh = 70, 56
        pad = 10
        return pygame.Rect(tb_left + 13, tb_top + 20 + index * (bh + pad), bw, bh)

    def _stamp_selector_rect(self, index):
        if isinstance(self.page_rect, pygame.Rect):
            pr_right, pr_top = self.page_rect.right, self.page_rect.top
        else:
            pr_right, pr_top = self.page_rect[0] + self.page_rect[2], self.page_rect[1]
        cols = 2
        sw = 64
        pad = 8
        row = index // cols
        col = index % cols
        base_x = pr_right - 160
        base_y = pr_top + 20
        return pygame.Rect(base_x + col * (sw + pad), base_y + row * (sw + pad), sw, sw)

    def _stamp_selector_rect_by_index(self, index):
        if isinstance(self.page_rect, pygame.Rect):
            pr_right, pr_top = self.page_rect.right, self.page_rect.top
        else:
            pr_right, pr_top = self.page_rect[0] + self.page_rect[2], self.page_rect[1]
        px = pr_right - 184
        py = pr_top + 10
        return pygame.Rect(px + 8, py + 30 + index * 68, 64, 60)

    def draw(self):
        self.tick += 1
        self.screen.fill((25, 15, 8))

        warm = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        warm.fill((100, 50, 10, 30))
        self.screen.blit(warm, (0, 0))

        if isinstance(self.page_rect, pygame.Rect):
            pr_left, pr_top = int(self.page_rect.left), int(self.page_rect.top)
            pr_width, pr_height = int(self.page_rect.width), int(self.page_rect.height)
            pr_right = int(self.page_rect.right)
            pr_centerx = int(self.page_rect.centerx)
            pr_centery = int(self.page_rect.centery)
        else:
            pr_left, pr_top, pr_width, pr_height = int(self.page_rect[0]), int(self.page_rect[1]), int(self.page_rect[2]), int(self.page_rect[3])
            pr_right = pr_left + pr_width
            pr_centerx = pr_left + (pr_width // 2)
            pr_centery = pr_top + (pr_height // 2)

        safe_rect = pygame.Rect(pr_left, pr_top, pr_width, pr_height)
        draw_page_frame(self.screen, safe_rect)

        if not self.doc:
            msg = self.fonts["body"].render("Could not load PDF.", False, RED)
            self.screen.blit(msg, msg.get_rect(center=safe_rect.center))
        elif self.page_surf:
            ps = self.page_surf
            dest = pygame.Rect(
                pr_centerx - ps.get_width()//2,
                pr_centery - ps.get_height()//2,
                ps.get_width(), ps.get_height()
            )
            self.screen.blit(ps, dest)

            tint = pygame.Surface(dest.size, pygame.SRCALPHA)
            tint.fill((160, 100, 30, 22))
            self.screen.blit(tint, dest)

            for stamp in self.stamps_on_page:
                sx = int(pr_left + stamp["x"] * pr_width)
                sy = int(pr_top  + stamp["y"] * pr_height)
                stype = stamp["stamp_type"]
                if stype.startswith("custom_"):
                    try:
                        sid = int(stype.split("_", 1)[1])
                        cs = next((c for c in self.custom_stamps if c["id"] == sid), None)
                    except Exception:
                        cs = None
                    sz = 40
                    r = pygame.Rect(sx - sz//2, sy - sz//2, sz, sz)
                    col = cs["color"] if cs else (150, 100, 50)
                    pygame.draw.rect(self.screen, col, r, border_radius=5)
                    pygame.draw.rect(self.screen, GOLD, r, 2, border_radius=5)
                    sym = cs["symbol"] if cs else "?"
                    sym_s = self.fonts["small"].render(sym[:2], False, CREAM)
                    self.screen.blit(sym_s, sym_s.get_rect(center=r.center))
                else:
                    ss = make_stamp_surface(stype, 40)
                    self.screen.blit(ss, (sx - 20, sy - 20))

            if self.line_marker_y and self.line_marker_y > 0:
                try:
                    m_w = max(10, int(pr_width))
                    marker_y = int(pr_top + float(self.line_marker_y) * pr_height)
                    marker_surf = pygame.Surface((m_w, 4), pygame.SRCALPHA)
                    marker_surf.fill((255, 80, 80, 160))
                    self.screen.blit(marker_surf, (int(pr_left), int(marker_y)))
                    pygame.draw.polygon(self.screen, (255, 80, 80),
                        [(int(pr_left) - 12, int(marker_y) - 6),
                         (int(pr_left), int(marker_y)),
                         (int(pr_left) - 12, int(marker_y) + 6)])
                except Exception as e:
                    pass

        if self.active_tool == TOOL_PEN:
            self._draw_pen_overlay()
        elif self.active_tool == TOOL_NOTEPAD:
            self._draw_notepad_overlay()
        elif self.active_tool == TOOL_STAMPS:
            self._draw_stamp_picker()
        elif self.active_tool == TOOL_BOOKMARK:
            hint = self.fonts["small"].render("Click on the page to place a line marker", False, GOLD)
            self.screen.blit(hint, hint.get_rect(centerx=pr_centerx, y=pr_top + pr_height + 8))

        self._draw_toolbar()
        self._draw_nav()
        self._draw_page_info()

        for bm in self.bookmarks:
            if bm["page"] == self.current_page:
                bm_y = int(pr_top + bm["line_y"] * pr_height)
                pygame.draw.polygon(self.screen, GOLD,
                    [(int(pr_right), int(bm_y) - 6),
                     (int(pr_right) + 14, int(bm_y)),
                     (int(pr_right), int(bm_y) + 6)])

        if self.show_review:
            self._draw_review_panel()

        if self.show_edit_book:
            self._draw_edit_book_panel()

        if self.show_custom_stamp:
            self._draw_custom_stamp_panel()

    def _draw_toolbar(self):
        if isinstance(self.toolbar_rect, pygame.Rect):
            tb_left, tb_top, tb_width, tb_height = self.toolbar_rect.left, self.toolbar_rect.top, self.toolbar_rect.width, self.toolbar_rect.height
        else:
            tb_left, tb_top, tb_width, tb_height = self.toolbar_rect[0], self.toolbar_rect[1], self.toolbar_rect[2], self.toolbar_rect[3]

        panel = pygame.Surface((tb_width, tb_height), pygame.SRCALPHA)
        panel.fill((40, 25, 12, 200))
        pygame.draw.rect(panel, GOLD, (0, 0, tb_width, tb_height), 2)
        self.screen.blit(panel, (int(tb_left), int(tb_top)))

        tool_labels = [
            ("✏", "Pen"),
            ("🔖", "Mark"),
            ("📓", "Notes"),
            ("★", "Stamps"),
        ]
        tools = [TOOL_PEN, TOOL_BOOKMARK, TOOL_NOTEPAD, TOOL_STAMPS]
        mx, my = pygame.mouse.get_pos()

        for i, (icon, label) in enumerate(tool_labels):
            tr = self._tool_rect(i)
            active = (self.active_tool == tools[i])
            bg = GOLD if active else (60, 38, 22)
            border = BROWN_DARK if active else BROWN_LIGHT
            pygame.draw.rect(self.screen, bg, tr, border_radius=4)
            pygame.draw.rect(self.screen, border, tr, 2, border_radius=4)
            icon_s = self.fonts["body"].render(icon, False, BROWN_DARK if active else GOLD)
            lbl_s  = self.fonts["small"].render(label, False, BROWN_DARK if active else CREAM)
            self.screen.blit(icon_s, icon_s.get_rect(centerx=tr.centerx, y=tr.top + 4))
            self.screen.blit(lbl_s, lbl_s.get_rect(centerx=tr.centerx, y=tr.top + 32))

    def _draw_nav(self):
        mx, my = pygame.mouse.get_pos()
        back_btn = pygame.Rect(10, SCREEN_H - 44, 80, 34)
        pixel_button(self.screen, back_btn, "← Back", self.fonts["small"], back_btn.collidepoint(mx, my))

        prev_btn = pygame.Rect(10, SCREEN_H//2 - 24, 44, 48)
        next_btn = pygame.Rect(SCREEN_W - 168, SCREEN_H//2 - 24, 44, 48)

        for btn, lbl in [(prev_btn, "◀"), (next_btn, "▶")]:
            hover = btn.collidepoint(mx, my)
            pygame.draw.rect(self.screen, GOLD if hover else BROWN_MID, btn, border_radius=6)
            pygame.draw.rect(self.screen, BROWN_DARK, btn, 2, border_radius=6)
            s = self.fonts["body"].render(lbl, False, BROWN_DARK if hover else CREAM)
            self.screen.blit(s, s.get_rect(center=btn.center))

    def _draw_page_info(self):
        if isinstance(self.page_rect, pygame.Rect):
            pr_left = self.page_rect.left
        else:
            pr_left = self.page_rect[0]

        mx, my = pygame.mouse.get_pos()
        info = f"Page {self.current_page + 1} of {self.total_pages} — {self.book.get('title', '')}"
        info_s = self.fonts["small"].render(info, False, GOLD_LIGHT)
        bar_w = info_s.get_width() + 130
        bar = pygame.Surface((bar_w, 24), pygame.SRCALPHA)
        bar.fill((30, 18, 10, 160))
        self.screen.blit(bar, (int(pr_left), SCREEN_H - 30))
        self.screen.blit(info_s, (int(pr_left) + 10, SCREEN_H - 26))

        self._edit_info_btn_rect = pygame.Rect(int(pr_left) + info_s.get_width() + 18, SCREEN_H - 30, 90, 22)
        pixel_button(self.screen, self._edit_info_btn_rect, "Edit Info", self.fonts["small"],
                     self._edit_info_btn_rect.collidepoint(mx, my))

    def _draw_pen_overlay(self):
        nf = self.note_field
        panel = pygame.Surface((nf.rect.width + 20, nf.rect.height + 60), pygame.SRCALPHA)
        panel.fill((30, 18, 8, 220))
        pygame.draw.rect(panel, GOLD, (0, 0, panel.get_width(), panel.get_height()), 2)
        self.screen.blit(panel, (nf.rect.left - 10, nf.rect.top - 30))

        hdr = self.fonts["small"].render(f"Write a note — {2700 - len(nf.text)} chars left", False, GOLD)
        self.screen.blit(hdr, (nf.rect.left, nf.rect.top - 24))

        nf.active = True
        pygame.draw.rect(self.screen, (240, 230, 200), nf.rect)
        pygame.draw.rect(self.screen, GOLD, nf.rect, 2)

        lines = []
        words = nf.text.split(" ")
        line = ""
        for w in words:
            test = line + " " + w if line else w
            if self.fonts["small"].size(test)[0] < nf.rect.width - 12:
                line = test
            else:
                lines.append(line)
                line = w
        if line:
            lines.append(line)
        for li, ln in enumerate(lines[:6]):
            s = self.fonts["small"].render(ln, False, BROWN_DARK)
            self.screen.blit(s, (nf.rect.left + 6, nf.rect.top + 4 + li * 18))

        if (self.tick // 30) % 2 == 0:
            last_line = lines[-1] if lines else ""
            cx = nf.rect.left + 6 + self.fonts["small"].size(last_line)[0]
            cy_top = nf.rect.top + 4 + max(0, len(lines)-1) * 18
            pygame.draw.line(self.screen, BROWN_DARK, (cx, cy_top), (cx, cy_top + 16), 2)

        save_btn = pygame.Rect(nf.rect.left + 10, nf.rect.bottom + 8, 100, 32)
        mx, my = pygame.mouse.get_pos()
        pixel_button(self.screen, save_btn, "Save Note", self.fonts["small"], save_btn.collidepoint(mx, my))

    def _draw_notepad_overlay(self):
        if isinstance(self.page_rect, pygame.Rect):
            pr_centerx, pr_centery = self.page_rect.centerx, self.page_rect.centery
        else:
            pr_centerx = self.page_rect[0] + (self.page_rect[2] // 2)
            pr_centery = self.page_rect[1] + (self.page_rect[3] // 2)

        panel_w, panel_h = 480, 400
        px = pr_centerx - panel_w//2
        py = pr_centery - panel_h//2

        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((40, 25, 12, 230))
        pygame.draw.rect(panel, GOLD, (0, 0, panel_w, panel_h), 2)
        self.screen.blit(panel, (px, py))

        hdr = self.fonts["body"].render(f"~ Notes for '{self.book.get('title', '')[:20]}' ~", False, GOLD)
        self.screen.blit(hdr, hdr.get_rect(centerx=px + panel_w//2, y=py + 10))
        pygame.draw.line(self.screen, GOLD, (px + 10, py + 38), (px + panel_w - 10, py + 38), 1)

        page_notes = [n for n in self.notes if n["page"] == self.current_page]
        all_notes = page_notes + [n for n in self.notes if n["page"] != self.current_page]

        clip = pygame.Rect(px + 8, py + 44, panel_w - 16, panel_h - 60)
        self.screen.set_clip(clip)
        y_off = py + 46 - self.note_scroll * 22

        for note in all_notes:
            date_s = self.fonts["small"].render(
                f"p.{note['page']+1} — {note['created_at'][:10]}", False, GOLD_LIGHT)
            self.screen.blit(date_s, (px + 12, y_off))
            y_off += 18
            text = note["content"]
            while text:
                chunk = text[:60]
                text = text[60:]
                ts = self.fonts["small"].render(chunk, False, CREAM)
                self.screen.blit(ts, (px + 12, y_off))
                y_off += 18
            pygame.draw.line(self.screen, BROWN_LIGHT,
                             (px + 10, y_off + 2), (px + panel_w - 10, y_off + 2), 1)
            y_off += 10

        self.screen.set_clip(None)

        close_btn = pygame.Rect(px + panel_w - 40, py + 6, 30, 26)
        pygame.draw.rect(self.screen, BROWN_MID, close_btn)
        pygame.draw.rect(self.screen, GOLD, close_btn, 1)
        xl = self.fonts["small"].render("✕", False, CREAM)
        self.screen.blit(xl, xl.get_rect(center=close_btn.center))

    def _draw_stamp_picker(self):
        if isinstance(self.page_rect, pygame.Rect):
            pr_right, pr_top = self.page_rect.right, self.page_rect.top
        else:
            pr_right = self.page_rect[0] + self.page_rect[2]
            pr_top = self.page_rect[1]

        all_stamps_list = list(STAMP_DATA.items()) + [
            (f"custom_{s['id']}", {"name": s["label"][:12], "color": tuple(s["color"]), "accent": GOLD, "symbol": s["symbol"]})
            for s in self.custom_stamps
        ]

        panel_w = 170
        panel_h = len(all_stamps_list) * 72 + 90
        px = pr_right - 184
        py = pr_top + 10

        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((40, 25, 12, 220))
        pygame.draw.rect(panel, GOLD, (0, 0, panel_w, panel_h), 2)
        self.screen.blit(panel, (px, py))

        hdr = self.fonts["small"].render("Pick a stamp:", False, GOLD)
        self.screen.blit(hdr, (px + 8, py + 8))

        mx, my = pygame.mouse.get_pos()
        for i, (stype, info) in enumerate(all_stamps_list):
            sr = pygame.Rect(px + 8, py + 30 + i * 68, 64, 60)
            if stype.startswith("custom_"):
                col = info["color"] if len(info["color"]) == 3 else info["color"][:3]
                pygame.draw.rect(self.screen, col, sr, border_radius=6)
                pygame.draw.rect(self.screen, GOLD, sr, 2, border_radius=6)
                sym_s = self.fonts["body"].render(info["symbol"][:2], False, CREAM)
                self.screen.blit(sym_s, sym_s.get_rect(center=sr.center))
            else:
                ss = make_stamp_surface(stype, 52)
                self.screen.blit(ss, (sr.left + 4, sr.top + 4))
            if self.selected_stamp == stype:
                pygame.draw.rect(self.screen, GOLD, sr, 2)
            name_s = self.fonts["small"].render(info["name"][:12], False, CREAM)
            self.screen.blit(name_s, (sr.right + 4, sr.centery - 8))

        new_btn = pygame.Rect(px + 8, py + panel_h - 68, panel_w - 16, 26)
        pixel_button(self.screen, new_btn, "+ New Stamp", self.fonts["small"], new_btn.collidepoint(mx, my))

        inst1 = self.fonts["small"].render("Click page to add", False, GOLD_LIGHT)
        inst2 = self.fonts["small"].render("Right click to del", False, RED)
        self.screen.blit(inst1, inst1.get_rect(centerx=px + panel_w//2, y=py + panel_h - 38))
        self.screen.blit(inst2, inst2.get_rect(centerx=px + panel_w//2, y=py + panel_h - 22))

        self._stamp_new_btn_rect    = new_btn
        self._all_stamps_list_cache = all_stamps_list

    def _draw_edit_book_panel(self):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        self.screen.blit(overlay, (0, 0))

        panel_w, panel_h = 420, 240
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

        self.edit_title_field.rect  = pygame.Rect(SCREEN_W//2 - 170, py + 60, 340, 34)
        self.edit_author_field.rect = pygame.Rect(SCREEN_W//2 - 170, py + 125, 340, 34)
        self.edit_title_field.draw(self.screen, self.fonts["small"])
        self.edit_author_field.draw(self.screen, self.fonts["small"])

        mx, my = pygame.mouse.get_pos()
        save_btn   = pygame.Rect(SCREEN_W//2 - 90, py + 185, 160, 36)
        cancel_btn = pygame.Rect(SCREEN_W//2 + 80, py + 185, 100, 36)
        pixel_button(self.screen, save_btn,   "Save Changes", self.fonts["small"], save_btn.collidepoint(mx, my))
        pixel_button(self.screen, cancel_btn, "Cancel",       self.fonts["small"], cancel_btn.collidepoint(mx, my))

        if self.edit_book_msg:
            color = GREEN_MID if "Saved" in self.edit_book_msg else RED
            m = self.fonts["small"].render(self.edit_book_msg, False, color)
            self.screen.blit(m, m.get_rect(centerx=SCREEN_W//2, y=py + 230))

    def _draw_custom_stamp_panel(self):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        self.screen.blit(overlay, (0, 0))

        panel_w, panel_h = 440, 260
        px = SCREEN_W//2 - panel_w//2
        py = 280
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((40, 25, 12, 240))
        pygame.draw.rect(panel, GOLD, (0, 0, panel_w, panel_h), 3)
        for cx, cy in [(0,0),(panel_w-8,0),(0,panel_h-8),(panel_w-8,panel_h-8)]:
            pygame.draw.rect(panel, GOLD, (cx, cy, 8, 8))
        self.screen.blit(panel, (px, py))

        hdr = self.fonts["body"].render("~ Create Custom Stamp ~", False, GOLD)
        self.screen.blit(hdr, hdr.get_rect(centerx=SCREEN_W//2, y=py + 14))

        sub = self.fonts["small"].render("Label                    Symbol", False, GOLD_LIGHT)
        self.screen.blit(sub, (SCREEN_W//2 - 110, py + 44))

        cx2 = SCREEN_W // 2
        self.custom_stamp_label.rect  = pygame.Rect(cx2 - 110, py + 60, 200, 30)
        self.custom_stamp_symbol.rect = pygame.Rect(cx2 + 100, py + 60, 60, 30)
        self.custom_stamp_label.draw(self.screen, self.fonts["small"])
        self.custom_stamp_symbol.draw(self.screen, self.fonts["small"])

        color_lbl = self.fonts["small"].render("Pick a colour:", False, GOLD_LIGHT)
        self.screen.blit(color_lbl, (cx2 - 110, py + 102))

        for i, col in enumerate(CUSTOM_STAMP_COLORS):
            cr = pygame.Rect(cx2 - 110 + i * 36, py + 118, 28, 28)
            pygame.draw.rect(self.screen, col, cr, border_radius=4)
            if i == self.custom_stamp_color_idx:
                pygame.draw.rect(self.screen, GOLD, cr, 2, border_radius=4)
            else:
                pygame.draw.rect(self.screen, BROWN_DARK, cr, 1, border_radius=4)

        preview_col = CUSTOM_STAMP_COLORS[self.custom_stamp_color_idx]
        pv_rect = pygame.Rect(cx2 + 110, py + 110, 44, 44)
        pygame.draw.rect(self.screen, preview_col, pv_rect, border_radius=6)
        pygame.draw.rect(self.screen, GOLD, pv_rect, 2, border_radius=6)
        sym_txt = self.custom_stamp_symbol.text or "?"
        sym_s = self.fonts["body"].render(sym_txt, False, CREAM)
        self.screen.blit(sym_s, sym_s.get_rect(center=pv_rect.center))

        mx, my = pygame.mouse.get_pos()
        save_btn   = pygame.Rect(cx2 - 90, py + 200, 160, 34)
        cancel_btn = pygame.Rect(cx2 + 80, py + 200, 90, 34)
        pixel_button(self.screen, save_btn,   "Create Stamp", self.fonts["small"], save_btn.collidepoint(mx, my))
        pixel_button(self.screen, cancel_btn, "Cancel",       self.fonts["small"], cancel_btn.collidepoint(mx, my))

        if self.custom_stamp_msg:
            m = self.fonts["small"].render(self.custom_stamp_msg, False, RED)
            self.screen.blit(m, m.get_rect(centerx=SCREEN_W//2, y=py + 244))

    def _handle_review_event(self, event):
        self.review_text_field.handle_event(event)
        self.dedication_field.handle_event(event)

        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            for i in range(5):
                actual = pygame.Rect(SCREEN_W//2 - 80 + i * 22, 278, 18, 18)
                if actual.collidepoint(mx, my):
                    self.review_rating = i + 1

            save_btn = pygame.Rect(SCREEN_W//2 - 80, 548, 160, 36)
            skip_btn = pygame.Rect(SCREEN_W//2 - 40, 598, 80, 28)
            if save_btn.collidepoint(mx, my) and self.review_rating > 0:
                self.db.add_review(
                    self.book["id"], self.user["id"],
                    self.review_rating,
                    self.review_text_field.text,
                    self.dedication_field.text
                )
                self.show_review = False
                return ("back",)
            if skip_btn.collidepoint(mx, my):
                self.show_review = False
                return ("back",)

        if event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            self.review_hover_star = -1
            for i in range(5):
                sr = pygame.Rect(SCREEN_W//2 - 80 + i * 22, 278, 18, 18)
                if sr.collidepoint(mx, my):
                    self.review_hover_star = i

        return None

    def _draw_review_panel(self):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        panel_w, panel_h = 480, 420
        px = SCREEN_W//2 - panel_w//2
        py = SCREEN_H//2 - panel_h//2

        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((40, 25, 12, 235))
        pygame.draw.rect(panel, GOLD, (0, 0, panel_w, panel_h), 3)
        self.screen.blit(panel, (px, py))

        hdr = self.fonts["body"].render("~ Finished! Leave a review ~", False, GOLD)
        self.screen.blit(hdr, hdr.get_rect(centerx=SCREEN_W//2, y=py + 14))

        book_lbl = self.fonts["small"].render(f'"{self.book.get("title", "")}" by {self.book.get("author", "")}',
                                              False, CREAM)
        self.book_lbl_rect = book_lbl.get_rect(centerx=SCREEN_W//2, y=py + 44)
        self.screen.blit(book_lbl, self.book_lbl_rect)

        rating_lbl = self.fonts["small"].render("Your rating:", False, GOLD_LIGHT)
        self.screen.blit(rating_lbl, (SCREEN_W//2 - 180, 278))

        display_r = self.review_hover_star + 1 if self.review_hover_star >= 0 else self.review_rating
        draw_star_rating(self.screen, SCREEN_W//2 - 80, 278, display_r)

        rev_lbl = self.fonts["small"].render("Your review (optional):", False, GOLD_LIGHT)
        self.screen.blit(rev_lbl, (SCREEN_W//2 - 200, 326))

        pygame.draw.rect(self.screen, (240, 230, 200), self.review_text_field.rect)
        pygame.draw.rect(self.screen, GOLD if self.review_text_field.active else BROWN_LIGHT,
                         self.review_text_field.rect, 2)
        lines = self.review_text_field.text.split("\n")
        for li, ln in enumerate(lines[:6]):
            s = self.fonts["small"].render(ln[:60], False, BROWN_DARK)
            self.screen.blit(s, (self.review_text_field.rect.left + 6,
                                 self.review_text_field.rect.top + 4 + li * 18))

        ded_lbl = self.fonts["small"].render("Dedicate this book (optional):", False, GOLD_LIGHT)
        self.screen.blit(ded_lbl, (SCREEN_W//2 - 200, 480))
        self.dedication_field.draw(self.screen, self.fonts["small"])

        mx, my = pygame.mouse.get_pos()
        save_btn = pygame.Rect(SCREEN_W//2 - 80, 548, 160, 36)
        pixel_button(self.screen, save_btn, "Save Review", self.fonts["small"],
                     save_btn.collidepoint(mx, my))

        skip_btn = pygame.Rect(SCREEN_W//2 - 40, 598, 80, 28)
        skip_lbl = self.fonts["small"].render("Skip →", False, GOLD_LIGHT)
        self.screen.blit(skip_lbl, skip_lbl.get_rect(centerx=SCREEN_W//2, y=602))