import pygame
from constants import *


def draw_pixel_border(surf, rect, thickness=3, color=BROWN_DARK, inner_color=BROWN_LIGHT):
    r = pygame.Rect(rect)
    for i in range(thickness):
        pygame.draw.rect(surf, color, r.inflate(0, 0), 1)
        r = r.inflate(-2, -2)
    pygame.draw.rect(surf, inner_color, r, 1)


def pixel_panel(surf, rect, bg=CREAM_DARK, border=BROWN_DARK, corner=GOLD):
    r = pygame.Rect(rect)
    pygame.draw.rect(surf, bg, r)
    pygame.draw.rect(surf, border, r, 3)
    cs = 6
    for cx, cy in [(r.left, r.top), (r.right-cs, r.top),
                   (r.left, r.bottom-cs), (r.right-cs, r.bottom-cs)]:
        pygame.draw.rect(surf, corner, (cx, cy, cs, cs))


def pixel_button(surf, rect, text, font, hover=False, pressed=False):
    r = pygame.Rect(rect)
    if pressed:
        bg, border, tc = BROWN_MID, BROWN_DARK, CREAM
        r = r.move(1, 1)
    elif hover:
        bg, border, tc = GOLD, BROWN_DARK, BROWN_DARK
    else:
        bg, border, tc = CREAM_DARK, BROWN_DARK, BROWN_DARK
    pygame.draw.rect(surf, bg, r)
    pygame.draw.rect(surf, border, r, 2)
    for cx, cy in [(r.left, r.top), (r.right-4, r.top),
                   (r.left, r.bottom-4), (r.right-4, r.bottom-4)]:
        pygame.draw.rect(surf, GOLD if not pressed else BROWN_LIGHT, (cx, cy, 4, 4))
    lbl = font.render(text, False, tc)
    surf.blit(lbl, lbl.get_rect(center=r.center))


def draw_pixel_text_input(surf, rect, text, font, active=False, label=""):
    r = pygame.Rect(rect)
    bg = (240, 230, 200) if active else CREAM
    border = GOLD if active else BROWN_LIGHT
    pygame.draw.rect(surf, bg, r)
    pygame.draw.rect(surf, border, r, 2)
    if label:
        lbl_s = font.render(label, False, BROWN_DARK)
        surf.blit(lbl_s, (r.left, r.top - 18))
    txt_s = font.render(text, False, BROWN_DARK)
    surf.blit(txt_s, (r.left + 6, r.centery - txt_s.get_height()//2))
    if active:
        cx = r.left + 6 + txt_s.get_width()
        if (pygame.time.get_ticks() // 500) % 2 == 0:
            pygame.draw.line(surf, BROWN_DARK, (cx, r.top+4), (cx, r.bottom-4), 2)


def draw_star_rating(surf, x, y, rating, max_stars=5, size=18):
    for i in range(max_stars):
        color = GOLD if i < rating else BROWN_LIGHT
        sx = x + i * (size + 4)
        pts = []
        import math
        for k in range(5):
            angle = math.pi/2 + k * 2*math.pi/5
            pts.append((sx + size//2 + int(size//2 * math.cos(angle)),
                        y  + size//2 - int(size//2 * math.sin(angle))))
            angle2 = math.pi/2 + (k+0.5)*2*math.pi/5
            pts.append((sx + size//2 + int(size//4 * math.cos(angle2)),
                        y  + size//2 - int(size//4 * math.sin(angle2))))
        pygame.draw.polygon(surf, color, pts)
        pygame.draw.polygon(surf, BROWN_DARK, pts, 1)
    return [pygame.Rect(x + i*(size+4), y, size, size) for i in range(max_stars)]


def make_badge_surface(badge_type):
    s = pygame.Surface((64, 64), pygame.SRCALPHA)
    if badge_type == "daily":
        pygame.draw.circle(s, GOLD, (32, 32), 28)
        pygame.draw.circle(s, BROWN_DARK, (32, 32), 28, 2)
        pygame.draw.polygon(s, BROWN_DARK, [(32,8),(38,24),(54,24),(42,34),(46,50),(32,40),(18,50),(22,34),(10,24),(26,24)])
    elif badge_type == "monthly":
        pygame.draw.rect(s, PURPLE_MID, (4, 4, 56, 56), border_radius=8)
        pygame.draw.rect(s, GOLD, (4, 4, 56, 56), 2, border_radius=8)
        pygame.draw.circle(s, GOLD, (32, 32), 16)
    elif badge_type == "yearly":
        pts = [(32,4),(58,20),(58,44),(32,60),(6,44),(6,20)]
        pygame.draw.polygon(s, GOLD, pts)
        pygame.draw.polygon(s, BROWN_DARK, pts, 2)
        pygame.draw.circle(s, PURPLE_MID, (32, 32), 14)
    elif badge_type == "bookworm":
        pygame.draw.ellipse(s, GREEN_MID, (4, 20, 56, 30))
        pygame.draw.ellipse(s, GREEN_DARK, (4, 20, 56, 30), 2)
        pygame.draw.circle(s, CREAM, (32, 20), 12)
        pygame.draw.circle(s, GREEN_DARK, (32, 20), 12, 2)
    else:
        pygame.draw.rect(s, GOLD_LIGHT, (8, 8, 48, 48), border_radius=6)
        pygame.draw.rect(s, BROWN_DARK, (8, 8, 48, 48), 2, border_radius=6)
    return s


STAMP_DATA = {
    "hobbit": {
        "name": "The Hobbit",
        "color": (120, 80, 40),
        "accent": (200, 160, 60),
        "symbol": "O",
    },
    "asoiaf": {
        "name": "A Song of Ice and Fire",
        "color": (60, 60, 120),
        "accent": (200, 50, 50),
        "symbol": "⚔",
    },
    "peter_rabbit": {
        "name": "Peter Rabbit",
        "color": (100, 160, 80),
        "accent": (200, 220, 180),
        "symbol": "🐰",
    },
    "alice": {
        "name": "Alice in Wonderland",
        "color": (120, 60, 160),
        "accent": (220, 180, 240),
        "symbol": "🃏",
    },
    "narnia": {
        "name": "Narnia",
        "color": (40, 80, 140),
        "accent": (200, 220, 255),
        "symbol": "✦",
    },
    "hp": {
        "name": "Harry Potter",
        "color": (100, 30, 30),
        "accent": (200, 160, 40),
        "symbol": "⚡",
    },
    "little_prince": {
        "name": "The Little Prince",
        "color": (180, 130, 20),
        "accent": (255, 230, 100),
        "symbol": "★",
    },
}


def make_stamp_surface(stamp_type, size=52):
    info = STAMP_DATA.get(stamp_type, {"color": BROWN_MID, "accent": GOLD, "symbol": "?", "name": ""})
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.rect(s, info["color"], (0, 0, size, size), border_radius=6)
    pygame.draw.rect(s, info["accent"], (0, 0, size, size), 2, border_radius=6)
    inner = pygame.Rect(4, 4, size-8, size-8)
    pygame.draw.rect(s, info["accent"], inner, 1, border_radius=4)
    for i in range(0, size, 6):
        pygame.draw.line(s, (*info["accent"], 60), (i, 0), (i, 2))
        pygame.draw.line(s, (*info["accent"], 60), (i, size-2), (i, size))
        pygame.draw.line(s, (*info["accent"], 60), (0, i), (2, i))
        pygame.draw.line(s, (*info["accent"], 60), (size-2, i), (size, i))
    return s


def draw_book_spine(surf, rect, title, author, color, font_small):
    r = pygame.Rect(rect)
    pygame.draw.rect(surf, color, r)
    pygame.draw.rect(surf, BROWN_DARK, r, 1)
    pygame.draw.line(surf, (*BROWN_DARK, 80), (r.left+2, r.top+4), (r.right-2, r.top+4))
    pygame.draw.line(surf, (*BROWN_DARK, 80), (r.left+2, r.bottom-4), (r.right-2, r.bottom-4))
    t = title[:12]
    ts = font_small.render(t, False, CREAM)
    surf.blit(ts, ts.get_rect(centerx=r.centerx, centery=r.centery))


def draw_pixel_leaf(surf, x, y, color=GREEN_MID, size=8):
    pts = [(x, y), (x+size, y-size//2), (x+size*2, y), (x+size, y+size//2)]
    pygame.draw.polygon(surf, color, pts)
    pygame.draw.line(surf, GREEN_DARK, (x, y), (x+size*2, y), 1)


def draw_page_frame(surf, rect):
    r = pygame.Rect(rect)
    frame_color = (160, 110, 60)
    shadow_color = (80, 50, 20)
    pygame.draw.rect(surf, shadow_color, r.move(4, 4))
    pygame.draw.rect(surf, (240, 225, 190), r)
    pygame.draw.rect(surf, frame_color, r, 4)
    corner_size = 16
    for cx, cy, da in [
        (r.left, r.top, 0),
        (r.right - corner_size, r.top, 90),
        (r.left, r.bottom - corner_size, 270),
        (r.right - corner_size, r.bottom - corner_size, 180),
    ]:
        cr = pygame.Rect(cx, cy, corner_size, corner_size)
        pygame.draw.rect(surf, GOLD, cr)
        pygame.draw.rect(surf, frame_color, cr, 2)
    for i in range(8, r.width - 8, 20):
        pygame.draw.rect(surf, GOLD, (r.left + i, r.top + 2, 4, 4))
        pygame.draw.rect(surf, GOLD, (r.left + i, r.bottom - 6, 4, 4))
    for i in range(8, r.height - 8, 20):
        pygame.draw.rect(surf, GOLD, (r.left + 2, r.top + i, 4, 4))
        pygame.draw.rect(surf, GOLD, (r.right - 6, r.top + i, 4, 4))


def draw_warm_overlay(surf):
    overlay = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
    overlay.fill((120, 60, 10, 35))
    surf.blit(overlay, (0, 0))


def draw_vine_decoration(surf, x, y, length=60, horizontal=False):
    color = GREEN_DARK
    leaf_color = GREEN_MID
    if horizontal:
        for i in range(0, length, 8):
            pygame.draw.circle(surf, color, (x + i, y + (i % 16 - 8)//2), 2)
            if i % 16 == 0:
                draw_pixel_leaf(surf, x + i - 4, y - 6, leaf_color, 6)
    else:
        for i in range(0, length, 8):
            pygame.draw.circle(surf, color, (x + (i % 16 - 8)//2, y + i), 2)
            if i % 16 == 0:
                draw_pixel_leaf(surf, x + 4, y + i - 4, leaf_color, 6)


def draw_firefly(surf, x, y, tick):
    phase = (tick // 30 + x * 7 + y * 13) % 60
    alpha = int(180 * abs(phase - 30) / 30)
    glow = pygame.Surface((10, 10), pygame.SRCALPHA)
    pygame.draw.circle(glow, (255, 255, 150, alpha), (5, 5), 4)
    surf.blit(glow, (x - 5, y - 5))


def draw_pixel_mushroom(surf, x, y, color=(180, 60, 180), size=12):
    stem_w = size // 3
    stem_h = size // 2
    pygame.draw.rect(surf, CREAM, (x - stem_w//2, y - stem_h, stem_w, stem_h))
    pygame.draw.ellipse(surf, color, (x - size//2, y - stem_h - size//2, size, size//2 + 4))
    pygame.draw.ellipse(surf, BROWN_DARK, (x - size//2, y - stem_h - size//2, size, size//2 + 4), 1)
    for dot in range(3):
        dx = x - size//3 + dot * (size//3)
        pygame.draw.circle(surf, WHITE, (dx, y - stem_h - size//4), 2)
