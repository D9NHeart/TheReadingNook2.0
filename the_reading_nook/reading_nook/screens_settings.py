import pygame
import os
from constants import *
from sprites import pixel_button
from screens_auth import InputField


class SettingsScreen:
    def __init__(self, screen, fonts, user, db):
        self.screen = screen
        self.fonts = fonts
        self.user = user
        self.db = db
        self.username_field = InputField((SCREEN_W//2 - 180, 200, 360, 34), "Username")
        self.email_field    = InputField((SCREEN_W//2 - 180, 265, 360, 34), "Email")
        self.pass_field     = InputField((SCREEN_W//2 - 180, 330, 360, 34), "New Password (leave blank to keep)", secret=True)
        self.username_field.text = user["username"]
        self.email_field.text    = user["email"]
        self.msg = ""
        self.confirm_delete = False
        self.confirm2 = False
        self.avatar_path = user.get("avatar_path", "")
        self.avatar_surf = None
        if self.avatar_path and os.path.exists(self.avatar_path):
            try:
                self.avatar_surf = pygame.image.load(self.avatar_path)
                self.avatar_surf = pygame.transform.scale(self.avatar_surf, (80, 80))
            except Exception:
                self.avatar_surf = None

    def handle_event(self, event):
        for f in [self.username_field, self.email_field, self.pass_field]:
            f.handle_event(event)

        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            back_btn    = pygame.Rect(20, 20, 80, 32)
            save_btn    = pygame.Rect(SCREEN_W//2 - 80, 400, 160, 36)
            avatar_btn  = pygame.Rect(SCREEN_W//2 - 180, 460, 200, 34)
            logout_btn  = pygame.Rect(SCREEN_W//2 - 80, 520, 160, 36)
            delete_btn  = pygame.Rect(SCREEN_W//2 - 80, 572, 160, 36)
            confirm_yes = pygame.Rect(SCREEN_W//2 - 120, 640, 100, 34)
            confirm_no  = pygame.Rect(SCREEN_W//2 + 20, 640, 100, 34)
            confirm2_yes = pygame.Rect(SCREEN_W//2 - 120, 710, 100, 34)
            confirm2_no  = pygame.Rect(SCREEN_W//2 + 20, 710, 100, 34)

            if back_btn.collidepoint(mx, my):
                return ("back",)
            if save_btn.collidepoint(mx, my):
                self._save_changes()
            if avatar_btn.collidepoint(mx, my):
                return ("pick_avatar",)
            if logout_btn.collidepoint(mx, my):
                return ("logout",)
            if delete_btn.collidepoint(mx, my) and not self.confirm_delete:
                self.confirm_delete = True
            if self.confirm_delete and not self.confirm2:
                if confirm_yes.collidepoint(mx, my):
                    self.confirm2 = True
                if confirm_no.collidepoint(mx, my):
                    self.confirm_delete = False
            if self.confirm2:
                if confirm2_yes.collidepoint(mx, my):
                    return ("delete_account",)
                if confirm2_no.collidepoint(mx, my):
                    self.confirm_delete = False
                    self.confirm2 = False
        return None

    def _save_changes(self):
        un = self.username_field.text.strip()
        em = self.email_field.text.strip()
        pw = self.pass_field.text
        if not un or not em:
            self.msg = "Username and email cannot be empty."
            return
        self.db.update_user_info(
            self.user["id"],
            username=un if un != self.user["username"] else None,
            email=em if em != self.user["email"] else None,
            password=pw if pw else None,
        )
        self.user["username"] = un
        self.user["email"] = em
        self.msg = "Changes saved!"

    def set_avatar(self, path):
        dest = self.db.update_avatar(self.user["id"], path)
        self.user["avatar_path"] = dest
        try:
            self.avatar_surf = pygame.image.load(dest)
            self.avatar_surf = pygame.transform.scale(self.avatar_surf, (80, 80))
        except Exception:
            self.avatar_surf = None
        self.msg = "Avatar updated!"

    def draw(self):
        self.screen.fill(BROWN_DARK)

        header = pygame.Surface((SCREEN_W, 64), pygame.SRCALPHA)
        header.fill((30, 18, 10, 200))
        self.screen.blit(header, (0, 0))
        pygame.draw.line(self.screen, GOLD, (0, 64), (SCREEN_W, 64), 2)

        title = self.fonts["title"].render("Settings", False, GOLD)
        self.screen.blit(title, title.get_rect(centerx=SCREEN_W//2, centery=32))

        mx, my = pygame.mouse.get_pos()
        back_btn = pygame.Rect(20, 16, 80, 32)
        pixel_button(self.screen, back_btn, "← Back", self.fonts["small"], back_btn.collidepoint(mx, my))

        av_x = SCREEN_W//2 + 120
        av_y = 120
        av_rect = pygame.Rect(av_x, av_y, 80, 80)
        if self.avatar_surf:
            self.screen.blit(self.avatar_surf, av_rect)
        else:
            pygame.draw.rect(self.screen, BROWN_MID, av_rect)
            nolbl = self.fonts["small"].render("No pic", False, CREAM)
            self.screen.blit(nolbl, nolbl.get_rect(center=av_rect.center))
        pygame.draw.rect(self.screen, GOLD, av_rect, 2)

        for f in [self.username_field, self.email_field, self.pass_field]:
            f.draw(self.screen, self.fonts["small"])

        save_btn = pygame.Rect(SCREEN_W//2 - 80, 400, 160, 36)
        pixel_button(self.screen, save_btn, "Save Changes", self.fonts["small"],
                     save_btn.collidepoint(mx, my))

        avatar_btn = pygame.Rect(SCREEN_W//2 - 180, 460, 200, 34)
        pixel_button(self.screen, avatar_btn, "Change Avatar", self.fonts["small"],
                     avatar_btn.collidepoint(mx, my))

        logout_btn = pygame.Rect(SCREEN_W//2 - 80, 520, 160, 36)
        pixel_button(self.screen, logout_btn, "Log Out", self.fonts["small"],
                     logout_btn.collidepoint(mx, my))

        delete_btn = pygame.Rect(SCREEN_W//2 - 80, 572, 160, 36)
        del_panel = pygame.Surface((160, 36), pygame.SRCALPHA)
        del_panel.fill((140, 40, 40, 200))
        self.screen.blit(del_panel, (SCREEN_W//2 - 80, 572))
        pygame.draw.rect(self.screen, (180, 60, 60), delete_btn, 2)
        del_lbl = self.fonts["small"].render("Delete Account", False, CREAM)
        self.screen.blit(del_lbl, del_lbl.get_rect(center=delete_btn.center))

        if self.confirm_delete:
            warn = self.fonts["body"].render("Are you sure? This cannot be undone.", False, RED)
            self.screen.blit(warn, warn.get_rect(centerx=SCREEN_W//2, y=618))
            yes1 = pygame.Rect(SCREEN_W//2 - 120, 640, 100, 34)
            no1  = pygame.Rect(SCREEN_W//2 + 20, 640, 100, 34)
            pixel_button(self.screen, yes1, "Yes, delete", self.fonts["small"], yes1.collidepoint(mx, my))
            pixel_button(self.screen, no1, "Cancel", self.fonts["small"], no1.collidepoint(mx, my))

        if self.confirm2:
            warn2 = self.fonts["body"].render("Really delete EVERYTHING?", False, RED)
            self.screen.blit(warn2, warn2.get_rect(centerx=SCREEN_W//2, y=686))
            yes2 = pygame.Rect(SCREEN_W//2 - 120, 710, 100, 34)
            no2  = pygame.Rect(SCREEN_W//2 + 20, 710, 100, 34)
            pixel_button(self.screen, yes2, "Yes, FINAL", self.fonts["small"], yes2.collidepoint(mx, my))
            pixel_button(self.screen, no2, "No, go back", self.fonts["small"], no2.collidepoint(mx, my))

        if self.msg:
            color = GREEN_MID if "saved" in self.msg.lower() or "updated" in self.msg.lower() else RED
            msg_s = self.fonts["small"].render(self.msg, False, color)
            self.screen.blit(msg_s, msg_s.get_rect(centerx=SCREEN_W//2, y=660))
