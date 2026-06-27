import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
DATA_DIR = os.path.join(BASE_DIR, "data")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")
IMAGES_DIR = os.path.join(ASSETS_DIR, "images")
BOOKS_DIR = os.path.join(DATA_DIR, "books")
USERS_DIR = os.path.join(DATA_DIR, "users")

for d in [DATA_DIR, BOOKS_DIR, USERS_DIR, FONTS_DIR, IMAGES_DIR]:
    os.makedirs(d, exist_ok=True)

SCREEN_W = 1280
SCREEN_H = 720
FPS = 60
TITLE = "The Reading Nook"

BROWN_DARK   = (62,  39,  35)
BROWN_MID    = (121, 85,  72)
BROWN_LIGHT  = (188, 143, 107)
CREAM        = (255, 248, 220)
CREAM_DARK   = (245, 230, 180)
GOLD         = (212, 175, 55)
GOLD_LIGHT   = (255, 215, 80)
GREEN_DARK   = (34,  85,  34)
GREEN_MID    = (76,  130, 76)
PURPLE_DARK  = (80,  40,  100)
PURPLE_MID   = (140, 80,  160)
BLUE_DARK    = (30,  50,  100)
BLUE_MID     = (60,  90,  160)
WHITE        = (255, 255, 255)
BLACK        = (0,   0,   0)
RED          = (180, 50,  50)
WARM_OVERLAY = (120, 60,  20, 55)

FONT_TITLE  = None
FONT_BODY   = None
FONT_SMALL  = None
FONT_PIXEL  = None
