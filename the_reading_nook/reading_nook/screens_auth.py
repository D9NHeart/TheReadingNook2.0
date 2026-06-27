import pygame
import os
from constants import *
from sprites import (pixel_panel, pixel_button, draw_pixel_text_input,
                     draw_vine_decoration, draw_firefly, draw_pixel_mushroom)


class InputField:
    def __init__(self, rect, label="", secret=False, max_len=64):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.text = ""
        self.active = False
        self.secret = secret
        self.max_len = max_len

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key not in (pygame.K_RETURN, pygame.K_TAB, pygame.K_ESCAPE):
                if len(self.text) < self.max_len:
                    self.text += event.unicode
        return False

    def draw(self, surf, font):
        display = ("*" * len(self.text)) if self.secret else self.text
        draw_pixel_text_input(surf, self.rect, display, font, self.active, self.label)


class LoginScreen:
    def __init__(self, screen, fonts, bg_image):
        self.screen = screen
        self.fonts = fonts
        self.bg = bg_image
        self.email_field = InputField((SCREEN_W//2 - 180, 310, 360, 34), "Email")
        self.pass_field = InputField((SCREEN_W//2 - 180, 380, 360, 34), "Password", secret=True)
        self.stay_logged = False
        self.error = ""
        self.mode = "login"
        self.tick = 0

        self.fireflies = [(80 + i * 90, 200 + (i*37)%180, i*23) for i in range(12)]

    def handle_event(self, event):
        for field in [self.email_field, self.pass_field]:
            field.handle_event(event)
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            login_btn = pygame.Rect(SCREEN_W//2 - 90, 440, 180, 38)
            toggle_btn = pygame.Rect(SCREEN_W//2 - 120, 498, 240, 28)
            stay_box = pygame.Rect(SCREEN_W//2 - 90, 489, 18, 18)
            if login_btn.collidepoint(mx, my):
                return ("login", self.email_field.text.strip(),
                        self.pass_field.text, self.stay_logged)
            if toggle_btn.collidepoint(mx, my):
                self.mode = "register"
                self.error = ""
            if stay_box.collidepoint(mx, my):
                self.stay_logged = not self.stay_logged
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            return ("login", self.email_field.text.strip(),
                    self.pass_field.text, self.stay_logged)
        return None

    def draw(self):
        self.tick += 1
        if self.bg:
            self.screen.blit(self.bg, (0, 0))
        else:
            self.screen.fill(BROWN_DARK)

        for fx, fy, fo in self.fireflies:
            draw_firefly(self.screen, fx, fy, self.tick + fo)

        panel_w, panel_h = 440, 340
        px = SCREEN_W//2 - panel_w//2
        py = 260
        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel_surf.fill((40, 25, 15, 210))
        pygame.draw.rect(panel_surf, GOLD, (0, 0, panel_w, panel_h), 3)
        for cx, cy in [(0,0),(panel_w-8,0),(0,panel_h-8),(panel_w-8,panel_h-8)]:
            pygame.draw.rect(panel_surf, GOLD, (cx, cy, 8, 8))
        self.screen.blit(panel_surf, (px, py))

        draw_vine_decoration(self.screen, px + 10, py + 20, 60)
        draw_vine_decoration(self.screen, px + panel_w - 20, py + 20, 60)
        draw_pixel_mushroom(self.screen, px + 30, py + panel_h - 10, (160, 50, 160), 10)
        draw_pixel_mushroom(self.screen, px + panel_w - 30, py + panel_h - 10, (80, 100, 180), 8)

     
        mode_lbl = self.fonts["body"].render(
            "Welcome back, traveller" if self.mode == "login" else "Join the Nook",
            False, GOLD_LIGHT
        )
        self.screen.blit(mode_lbl, mode_lbl.get_rect(centerx=SCREEN_W//2, y=py + 18))

        self.email_field.draw(self.screen, self.fonts["small"])
        self.pass_field.draw(self.screen, self.fonts["small"])

        btn_r = pygame.Rect(SCREEN_W//2 - 90, 440, 180, 38)
        mx, my = pygame.mouse.get_pos()
        hover = btn_r.collidepoint(mx, my)
        lbl = "Enter the Nook" if self.mode == "login" else "Create Account"
        pixel_button(self.screen, btn_r, lbl, self.fonts["small"], hover)

        stay_box = pygame.Rect(SCREEN_W//2 - 90, 489, 18, 18)
        pygame.draw.rect(self.screen, BROWN_DARK, stay_box)
        pygame.draw.rect(self.screen, BROWN_DARK, stay_box, 2)
        if self.stay_logged:
            pygame.draw.line(self.screen, GREEN_MID, stay_box.topleft, stay_box.bottomright, 2)
            pygame.draw.line(self.screen, GREEN_MID, stay_box.topright, stay_box.bottomleft, 2)
        stay_lbl = self.fonts["small"].render("Stay logged in", False, CREAM)
        self.screen.blit(stay_lbl, (SCREEN_W//2 - 68, 491))

        toggle_txt = "New here? Create an account →" if self.mode == "login" else "← Back to login"
        toggle_lbl = self.fonts["small"].render(toggle_txt, False, GOLD_LIGHT)
        self.screen.blit(toggle_lbl, toggle_lbl.get_rect(centerx=SCREEN_W//2, y=498))

        if self.error:
            err_lbl = self.fonts["small"].render(self.error, False, RED)
            self.screen.blit(err_lbl, err_lbl.get_rect(centerx=SCREEN_W//2, y=540))


class RegisterScreen:
    def __init__(self, screen, fonts, bg_image):
        self.screen = screen
        self.fonts = fonts
        self.bg = bg_image
        self.username_field = InputField((SCREEN_W//2 - 180, 290, 360, 34), "Username")
        self.email_field    = InputField((SCREEN_W//2 - 180, 355, 360, 34), "Email")
        self.pass_field     = InputField((SCREEN_W//2 - 180, 420, 360, 34), "Password", secret=True)
        self.pass2_field    = InputField((SCREEN_W//2 - 180, 485, 360, 34), "Confirm Password", secret=True)
        self.error = ""
        self.tick = 0
        self.fireflies = [(60 + i * 110, 180 + (i*47)%220, i*31) for i in range(10)]

    def handle_event(self, event):
        for f in [self.username_field, self.email_field, self.pass_field, self.pass2_field]:
            f.handle_event(event)
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            create_btn = pygame.Rect(SCREEN_W//2 - 100, 538, 200, 38)
            back_btn   = pygame.Rect(SCREEN_W//2 - 80, 586, 160, 28)
            if create_btn.collidepoint(mx, my):
                return ("register",
                        self.username_field.text.strip(),
                        self.email_field.text.strip(),
                        self.pass_field.text,
                        self.pass2_field.text)
            if back_btn.collidepoint(mx, my):
                return ("back",)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            return ("register",
                    self.username_field.text.strip(),
                    self.email_field.text.strip(),
                    self.pass_field.text,
                    self.pass2_field.text)
        return None

    def draw(self):
        self.tick += 1
        if self.bg:
            self.screen.blit(self.bg, (0, 0))
        else:
            self.screen.fill(BROWN_DARK)

        for fx, fy, fo in self.fireflies:
            draw_firefly(self.screen, fx, fy, self.tick + fo)

        panel_w, panel_h = 440, 380
        px = SCREEN_W//2 - panel_w//2
        py = 240
        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel_surf.fill((40, 25, 15, 215))
        pygame.draw.rect(panel_surf, GOLD, (0, 0, panel_w, panel_h), 3)
        self.screen.blit(panel_surf, (px, py))

        title_lbl = self.fonts["title"].render("The Reading Nook", False, GOLD)
        self.screen.blit(title_lbl, title_lbl.get_rect(centerx=SCREEN_W//2, y=170))

        hdr = self.fonts["body"].render("~ Join the Nook ~", False, GOLD_LIGHT)
        self.screen.blit(hdr, hdr.get_rect(centerx=SCREEN_W//2, y=py + 16))

        for f in [self.username_field, self.email_field, self.pass_field, self.pass2_field]:
            f.draw(self.screen, self.fonts["small"])

        btn_r = pygame.Rect(SCREEN_W//2 - 100, 538, 200, 38)
        mx, my = pygame.mouse.get_pos()
        pixel_button(self.screen, btn_r, "Create Account", self.fonts["small"],
                     btn_r.collidepoint(mx, my))

        back_r = pygame.Rect(SCREEN_W//2 - 80, 586, 160, 28)
        back_lbl = self.fonts["small"].render("← Back to login", False, GOLD_LIGHT)
        self.screen.blit(back_lbl, back_lbl.get_rect(centerx=SCREEN_W//2, y=590))

        if self.error:
            err_lbl = self.fonts["small"].render(self.error, False, RED)
            self.screen.blit(err_lbl, err_lbl.get_rect(centerx=SCREEN_W//2, y=630))
