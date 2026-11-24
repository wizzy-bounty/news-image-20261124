"""news-image-20261124 entry: "TUESDAY 24 NOVEMBER 2026 — The World in One Picture".

Draws one 1024x1024 PNG summing up the world news of Tuesday 24 November 2026:
36 stories (13 pictured with flat pictograms and key numbers, 23 one-liners),
a numbered dot-grid world map, a UTC timeline and a DATE CHECK box.

Python standard library only. Deterministic: no clock, no randomness, no
network. Writes exactly one file: <MAKEFUN_OUTPUT_DIR>/entry.png
(or /output/entry.png when the variable is unset).
"""

import base64
import os
import struct
import zlib

from fontdata import FONTS

W = 1024
H = 1024

# ---------------------------------------------------------------- palette
PAPER = (246, 241, 229)
CARD = (255, 253, 246)
INK = (20, 32, 46)
GRAY = (96, 104, 112)
NAVY = (18, 38, 63)
RED = (179, 57, 46)
WHITE = (255, 255, 255)

REGION_COLORS = {
    "EUROPE": (32, 80, 122),
    "CLIMATE": (46, 125, 91),
    "SPACE": (75, 58, 138),
    "ASIA": (179, 57, 46),
    "AMERICAS": (51, 96, 140),
    "AFRICA": (200, 137, 42),
    "MIDEAST": (122, 74, 140),
    "SPORT": (46, 125, 50),
    "BUSINESS": (91, 74, 138),
    "HEALTH": (46, 138, 107),
}
BADGE_COLORS = {
    "CONFIRMED": (38, 110, 62),
    "OFFICIAL": (32, 80, 122),
    "REPORTED": (166, 110, 20),
}

# ---------------------------------------------------------------- canvas
_buf = bytearray(W * H * 3)


def _set(x, y, color):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        _buf[i] = color[0]
        _buf[i + 1] = color[1]
        _buf[i + 2] = color[2]


def _blend(x, y, color, cov):
    """Paint color at pixel with coverage cov (0..255)."""
    if cov <= 0 or not (0 <= x < W and 0 <= y < H):
        return
    i = (y * W + x) * 3
    if cov >= 255:
        _buf[i] = color[0]
        _buf[i + 1] = color[1]
        _buf[i + 2] = color[2]
    else:
        inv = 255 - cov
        _buf[i] = (_buf[i] * inv + color[0] * cov) // 255
        _buf[i + 1] = (_buf[i + 1] * inv + color[1] * cov) // 255
        _buf[i + 2] = (_buf[i + 2] * inv + color[2] * cov) // 255


def rect(x, y, w, h, color):
    x0, y0 = max(0, int(x)), max(0, int(y))
    x1, y1 = min(W, int(x + w)), min(H, int(y + h))
    row = bytes(color) * max(0, x1 - x0)
    for yy in range(y0, y1):
        i = (yy * W + x0) * 3
        _buf[i:i + len(row)] = row


def rect_line(x, y, w, h, color, t=1):
    rect(x, y, w, t, color)
    rect(x, y + h - t, w, t, color)
    rect(x, y, t, h, color)
    rect(x + w - t, y, t, h, color)


def circle(cx, cy, r, color):
    r2 = r * r
    for yy in range(int(cy - r), int(cy + r) + 1):
        dy = yy - cy
        rem = r2 - dy * dy
        if rem < 0:
            continue
        dx = int(rem ** 0.5)
        rect(int(cx - dx), yy, dx * 2 + 1, 1, color)


def ring(cx, cy, r, color, t=2):
    r2o = r * r
    r2i = (r - t) * (r - t)
    for yy in range(int(cy - r), int(cy + r) + 1):
        for xx in range(int(cx - r), int(cx + r) + 1):
            d2 = (xx - cx) ** 2 + (yy - cy) ** 2
            if r2i <= d2 <= r2o:
                _set(xx, yy, color)


def line(x0, y0, x1, y1, color, t=1):
    steps = max(abs(x1 - x0), abs(y1 - y0), 1)
    r = max(0, t // 2)
    for s in range(steps + 1):
        xx = x0 + (x1 - x0) * s / steps
        yy = y0 + (y1 - y0) * s / steps
        if r == 0:
            _set(int(xx), int(yy), color)
        else:
            circle(xx, yy, r, color)


def poly(points, color):
    ys = [p[1] for p in points]
    y0, y1 = int(min(ys)), int(max(ys))
    n = len(points)
    for yy in range(y0, y1 + 1):
        xs = []
        for i in range(n):
            xa, ya = points[i]
            xb, yb = points[(i + 1) % n]
            if (ya <= yy < yb) or (yb <= yy < ya):
                xs.append(xa + (yy - ya) * (xb - xa) / (yb - ya))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            rect(int(xs[i]), yy, int(xs[i + 1]) - int(xs[i]) + 1, 1, color)


def tri(x0, y0, x1, y1, x2, y2, color):
    poly([(x0, y0), (x1, y1), (x2, y2)], color)


# ---------------------------------------------------------------- text
_glyph_cache = {}


def _glyph(font, size, ch):
    key = (font, size, ch)
    g = _glyph_cache.get(key)
    if g is None:
        adv, w, h, xo, yo, data = FONTS[font][str(size)][ch]
        raw = zlib.decompress(base64.b85decode(data)) if data else b""
        g = (adv, w, h, xo, yo, raw)
        _glyph_cache[key] = g
    return g


def text_w(s, font, size, tracking=0):
    total = 0
    for ch in s:
        total += _glyph(font, size, ch)[0] + tracking
    return total - (tracking if s else 0)


def text(x, y, s, font, size, color, tracking=0):
    """Draw text with (x, y) at the top of the glyph boxes' origin line."""
    cx = x
    for ch in s:
        adv, w, h, xo, yo, raw = _glyph(font, size, ch)
        if w and h:
            for yy in range(h):
                base = yy * w
                for xx in range(w):
                    cov = raw[base + xx]
                    if cov:
                        _blend(int(cx) + xo + xx, y + yo + yy, color, cov)
        cx += adv + tracking
    return cx - x


def text_c(cx, y, s, font, size, color, tracking=0):
    w = text_w(s, font, size, tracking)
    return text(cx - w // 2, y, s, font, size, color, tracking)


def text_r(rx, y, s, font, size, color, tracking=0):
    w = text_w(s, font, size, tracking)
    return text(rx - w, y, s, font, size, color, tracking)


def wrap(s, font, size, maxw):
    words = s.split()
    lines = []
    cur = ""
    for wd in words:
        trial = (cur + " " + wd).strip()
        if text_w(trial, font, size) <= maxw or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


def block(x, y, s, font, size, color, maxw, lh, max_lines=None):
    lines = wrap(s, font, size, maxw)
    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines]
    for i, ln in enumerate(lines):
        text(x, y + i * lh, ln, font, size, color)
    return len(lines)


# ---------------------------------------------------------------- png out
def save_png(path):
    raw = bytearray()
    stride = W * 3
    for yy in range(H):
        raw.append(0)
        raw += _buf[yy * stride:(yy + 1) * stride]

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as fh:
        fh.write(png)


# ---------------------------------------------------------------- stories
# (num, region, badge, headline, sub) — all from reporting dated Tue 24 Nov 2026
LEADS = [
    (1, "EUROPE", "OFFICIAL",
     "Ukraine strikes Russian warship off Libya",
     "Zelenskyy says drones sank a Russian warship near Libya, far from "
     "the front line. The UN warns Libya must not become a battleground. "
     "— wire reports"),
    (2, "CLIMATE", "CONFIRMED",
     "Climate talks end with no pact; Pacific pays",
     "COP31 closed in Antalya with no deal. Pacific leaders accuse "
     "Australia of betrayal; the UN chief: science allows no ambiguity. "
     "— PINA"),
    (3, "SPACE", "OFFICIAL",
     "China names crew: first foreign astronaut flies",
     "Crew: Tang Hongbo, Wu Yi and Pakistan's Zeeshan Ali, first foreign "
     "visitor to Tiangong. Liftoff Wed 08:18 Beijing. — Reuters"),
]

MEDIUMS = [
    (4, "ASIA", "CONFIRMED",
     "Indonesia charges ex-police chief with treason",
     "Listyo Sigit among 6 suspects in a wiretap plot. — Reuters",
     "6 SUSPECTS", (122, 46, 46), "scales"),
    (5, "HEALTH", "REPORTED",
     "Bangladesh vaccinates 50 million children",
     "Month-long typhoid drive vs drug-resistant strains. — Dhaka",
     "50M KIDS", (46, 107, 52), "syringe"),
    (6, "AMERICAS", "REPORTED",
     "ICE agents arrest travellers at Seattle airport",
     "'Out of control' scenes as agents detain passengers. — reports",
     "SEATTLE", (60, 75, 92), "plane"),
    (7, "EUROPE", "REPORTED",
     "Lagarde resigns; EU hunts new ECB chief",
     "Brussels opens search for a central-bank president. — reports",
     "ECB VACANCY", (122, 90, 23), "bank"),
    (8, "AFRICA", "REPORTED",
     "South Africa votes amid blackouts and anger",
     "Service-delivery fury tests the ruling ANC. — reports",
     "SA VOTES", (138, 77, 22), "ballot"),
    (9, "MIDEAST", "REPORTED",
     "Israeli strike kills UN worker in Gaza",
     "Agency staffer killed; 3 die at a Gaza police post. — agencies",
     "1 UN WORKER", (92, 85, 75), "crescent"),
    (10, "SPORT", "CONFIRMED",
     "Samoa rout Spain 90-22; Tonga win 55-19",
     "Pacific sides run riot in the Nations Championship. — PINA",
     "90-22", (31, 81, 48), "rugby"),
    (11, "BUSINESS", "REPORTED",
     "SK hynix leaps 20% amid Nvidia turmoil",
     "Chip shares whipsaw on Nvidia leadership reports. — reports",
     "+20%", (75, 46, 107), "chip"),
    (12, "ASIA", "CONFIRMED",
     "Malaysia to send 1,500 Myanmar nationals home",
     "3 navy ships due Dec 6-7; Türkiye says no. — Reuters",
     "1,500 HOME", (23, 97, 107), "ship"),
    (13, "ASIA", "REPORTED",
     "Army hunts ~100 missing in Himalayan flood",
     "At least 4 dead after mud tore down a mountain valley. — reports",
     "~100 MISSING", (51, 86, 107), "mountain"),
]

ALSO = [
    (14, "Fiji shuts every school 5 days as El Niño drought deepens"),
    (15, "All of Kanton Island, Kiribati, evacuated at a day's notice"),
    (16, "Australia-Vanuatu treaty loses bipartisan backing"),
    (17, "Seoul scrambles jets after Russian aircraft breach report"),
    (18, "Merz: Kremlin must halt provocations, missiles in Poland"),
    (19, "France confirms fatal bird-flu outbreak at a poultry farm"),
    (20, "UN chief: agree global AI rules within one year"),
    (21, "Mexico to try 'El Chapo Isidro' at home, defying US bid"),
    (22, "FAA lifts ground stop at Chicago O'Hare after staff snarl"),
    (23, "Deadly storm displaces thousands in a Brazilian town"),
    (24, "RSF drone strikes black out Sudan power stations"),
    (25, "Norway's top court voids climate-disputed oil licences"),
    (26, "Kenya signs deal for 293,600 Saudi job slots"),
    (27, "DR Congo's Tshisekedi enacts contested reform law"),
    (28, "Sahel states reopen dialogue with the ECOWAS bloc"),
    (29, "Ghana unveils 'Heritage Series' banknotes"),
    (30, "Inter lose 7-goal San Siro thriller; Tresoldi hat-trick"),
    (31, "Inglis & Carey put Australia on top in SA decider"),
    (32, "Fiji edge Italy for first Nations Championship win"),
    (33, "India holds 3rd place in the Asia Power Index"),
    (34, "MSCI: no decision yet on downgrading Indonesia"),
    (35, "North Korea may shut Swiss office in Pyongyang — KCNA"),
    (36, "Model of the year: South Sudan's Awar Odhiang"),
]

DATE_CHECK = [
    "COP31 talks themselves ended Sun 22 Nov — Tuesday's news is the fallout",
    "Trump dared Iran to test the Hormuz blockade — Sun 22 Nov",
    "US sanctions on Iran's shadow banks — unveiled Mon 23 Nov",
    "BepiColombo slipped into Mercury orbit — Mon 23 Nov",
    "Voyager 1 reached one light-day from Earth — 18 Nov",
    "Shenzhou-24 liftoff — Wed 25 Nov (crew named Tuesday)",
    "US midterm elections — Tue 3 Nov",
]

TIMELINE = ("01:03 Dhaka typhoid drive - 04:37 US Iran-bank curbs - "
            "05:09 Kyiv: Libya strike - 10:13 Progress MS-36 up* - "
            "15:55 Falcon 9 USSF-266* - 00:18 Wed Shenzhou-24 up*")

# map pins: story num -> (lon, lat)
PINS = {
    1: (20, 27), 2: (30, 37), 3: (100, 41), 4: (107, -6), 5: (90, 24),
    6: (-122, 47), 7: (8, 50), 8: (28, -26), 9: (34, 31), 10: (-172, -14),
    11: (127, 37), 12: (102, 3), 13: (79, 30),
}

# dot-grid world map: row -> [(col_start, col_end)] land spans.
# Grid: 72 cols (lon -180..180, 5 deg each), 25 rows (lat 85..-60).
LAND_SPANS = {
    0: [(8, 16), (24, 28), (44, 50), (56, 66)],
    1: [(6, 18), (25, 29), (38, 42), (44, 68)],
    2: [(5, 19), (26, 28), (38, 40), (42, 68)],
    3: [(2, 6), (8, 20), (35, 35), (37, 43), (44, 67)],
    4: [(5, 19), (36, 44), (45, 66), (65, 65)],
    5: [(6, 19), (36, 43), (44, 64)],
    6: [(7, 18), (35, 42), (43, 60), (64, 65)],
    7: [(7, 18), (36, 40), (42, 47), (52, 62), (64, 64)],
    8: [(7, 17), (35, 39), (41, 48), (52, 61), (62, 64)],
    9: [(7, 16), (34, 44), (44, 48), (50, 54), (55, 60)],
    10: [(8, 13), (33, 45), (45, 48), (50, 53), (55, 58)],
    11: [(22, 25), (34, 45), (51, 53), (55, 58)],
    12: [(22, 26), (35, 44), (55, 60)],
    13: [(22, 26), (36, 44), (56, 62)],
    14: [(22, 27), (37, 43), (57, 62), (63, 65)],
    15: [(23, 27), (37, 43), (59, 63)],
    16: [(23, 27), (38, 42), (58, 64)],
    17: [(23, 26), (38, 42), (58, 64)],
    18: [(23, 26), (39, 41), (59, 63)],
    19: [(23, 25), (39, 41), (60, 62)],
    20: [(23, 25), (39, 40), (60, 62)],
    21: [(23, 24), (68, 69)],
    22: [(23, 24), (68, 68)],
    23: [(23, 23)],
    24: [(23, 23)],
}


# ---------------------------------------------------------------- pictograms
FG = (245, 240, 225)
GOLD = (255, 190, 80)


def pic_warship(x, y, w, h):
    rect(x, y, w, h, (29, 78, 107))
    rect(x, y + h - 26, w, 26, (23, 62, 86))
    for i in range(6):
        rect(x + 12 + i * 52, y + h - 18, 26, 3, (70, 130, 160))
    dark = (13, 30, 44)
    hull = (172, 196, 210)
    poly([(x + 34, y + h - 34), (x + w - 46, y + h - 34),
          (x + w - 66, y + h - 17), (x + 50, y + h - 17)], hull)
    rect(x + 92, y + h - 48, 62, 14, hull)
    rect(x + 108, y + h - 60, 30, 12, hull)
    rect(x + 120, y + h - 78, 4, 18, hull)
    rect(x + 60, y + h - 44, 22, 10, hull)
    rect(x + 34, y + h - 34, w - 80, 3, dark)
    # drone top-right with dashed drop line
    dx, dy = x + w - 78, y + 16
    rect(dx, dy + 4, 26, 7, FG)
    for ox, oy in ((-8, 0), (30, 0), (-8, 12), (30, 12)):
        circle(dx + ox, dy + oy, 4, FG)
    for i in range(4):
        rect(dx + 10, dy + 20 + i * 9, 3, 5, GOLD)
    # burst at the bow
    bx, by = x + w - 50, y + h - 36
    for ang in range(0, 360, 45):
        import math
        ex = bx + int(17 * math.cos(math.radians(ang)))
        ey = by + int(17 * math.sin(math.radians(ang)))
        line(bx, by, ex, ey, GOLD, 3)
    circle(bx, by, 6, (255, 120, 50))
    text(x + 12, y + h - 52, "1 WARSHIP HIT", "sansb", 16, WHITE)


def pic_globe(x, y, w, h):
    rect(x, y, w, h, (23, 89, 79))
    circle(x + w - 36, y + 20, 11, GOLD)
    circle(x + 86, y + 58, 41, (14, 56, 48))
    ring(x + 86, y + 58, 41, FG, 3)
    land = (74, 160, 120)
    poly([(x + 58, y + 34), (x + 82, y + 28), (x + 88, y + 44),
          (x + 66, y + 50), (x + 56, y + 42)], land)
    poly([(x + 92, y + 58), (x + 112, y + 54), (x + 116, y + 70),
          (x + 98, y + 78), (x + 90, y + 66)], land)
    poly([(x + 62, y + 66), (x + 76, y + 64), (x + 78, y + 76),
          (x + 64, y + 78)], land)
    line(x + 84, y + 22, x + 92, y + 42, GOLD, 2)
    line(x + 92, y + 42, x + 84, y + 58, GOLD, 2)
    line(x + 84, y + 58, x + 94, y + 80, GOLD, 2)
    poly([(x + 150, y + h - 12), (x + 196, y + h - 34),
          (x + 242, y + h - 12)], (16, 64, 56))
    line(x + 196, y + h - 34, x + 196, y + h - 52, FG, 2)
    line(x + 196, y + h - 52, x + 210, y + h - 44, FG, 2)
    line(x + 196, y + h - 52, x + 184, y + h - 42, FG, 2)
    text(x + 150, y + 14, "NO PACT", "serifb", 30, WHITE)
    text(x + 152, y + 52, "COP31 - ANTALYA", "sansb", 10, GOLD)


def pic_rocket(x, y, w, h):
    rect(x, y, w, h, (35, 42, 94))
    for sx, sy in ((20, 18), (70, 40), (130, 14), (250, 30), (286, 60),
                   (40, 74), (268, 92), (160, 96), (96, 100)):
        rect(x + sx, y + sy, 3, 3, WHITE)
    rx, ry = x + 44, y + 14
    rect(rx, ry + 18, 26, 62, FG)
    tri(rx, ry + 18, rx + 26, ry + 18, rx + 13, ry, (220, 70, 50))
    circle(rx + 13, ry + 40, 6, (35, 42, 94))
    tri(rx, ry + 80, rx - 12, ry + 98, rx, ry + 62, (220, 70, 50))
    tri(rx + 26, ry + 80, rx + 38, ry + 98, rx + 26, ry + 62, (220, 70, 50))
    tri(rx + 4, ry + 80, rx + 22, ry + 80, rx + 13, ry + 104, GOLD)
    tri(rx + 7, ry + 80, rx + 19, ry + 80, rx + 13, ry + 96, (255, 120, 50))
    # station at top-right
    sx2, sy2 = x + w - 58, y + 12
    rect(sx2, sy2, 22, 9, FG)
    rect(sx2 - 26, sy2 + 2, 21, 6, (110, 150, 220))
    rect(sx2 + 27, sy2 + 2, 21, 6, (110, 150, 220))
    text(x + 92, y + 14, "FIRST", "serifb", 30, WHITE)
    text(x + 92, y + 50, "FOREIGN", "serifb", 30, WHITE)
    text(x + 92, y + 86, "ASTRONAUT", "serifb", 30, GOLD)


def pic_scales(x, y, s):
    line(x + s // 2, y + 4, x + s // 2, y + s - 8, FG, 2)
    line(x + 4, y + 10, x + s - 4, y + 10, FG, 2)
    for px in (x + 10, x + s - 10):
        line(px, y + 10, px - 6, y + 24, FG, 1)
        line(px, y + 10, px + 6, y + 24, FG, 1)
        line(px - 8, y + 24, px + 8, y + 24, GOLD, 2)
    rect(x + s // 2 - 10, y + s - 8, 20, 4, FG)


def pic_syringe(x, y, s):
    # needle at lower-left, barrel diagonal, plunger at upper-right
    line(x + 3, y + s - 4, x + 14, y + s - 15, GOLD, 2)
    line(x + 13, y + s - 14, x + 30, y + s - 31, FG, 7)
    line(x + 22, y + s - 26, x + 27, y + s - 21, (46, 107, 52), 2)
    line(x + 30, y + s - 31, x + 38, y + s - 39, FG, 3)
    line(x + 33, y + s - 42, x + 43, y + s - 32, FG, 3)
    circle(x + 10, y + 10, 4, GOLD)
    circle(x + 20, y + 16, 3, GOLD)


def pic_plane(x, y, s):
    cy = y + s // 2 + 2
    rect(x + 6, cy - 5, s - 18, 10, FG)
    tri(x + s - 12, cy - 5, x + s - 12, cy + 5, x + s - 3, cy, FG)
    circle(x + s - 13, cy, 3, (60, 75, 92))
    tri(x + 6, cy - 5, x + 16, cy - 5, x + 6, cy - 19, GOLD)
    tri(x + 6, cy + 5, x + 14, cy + 5, x + 6, cy + 13, GOLD)
    tri(x + s // 2 - 6, cy + 4, x + s // 2 + 9, cy + 4,
        x + s // 2, cy + 16, GOLD)
    for i in range(4):
        circle(x + 18 + i * 8, cy - 1, 2, (60, 75, 92))


def pic_bank(x, y, s):
    tri(x + 2, y + 14, x + s - 2, y + 14, x + s // 2, y + 2, FG)
    for i in range(3):
        rect(x + 8 + i * 13, y + 18, 5, 20, FG)
    rect(x + 3, y + 40, s - 6, 4, FG)


def pic_ballot(x, y, s):
    rect(x + 10, y + 6, 18, 14, FG)
    line(x + 14, y + 13, x + 18, y + 17, (138, 77, 22), 2)
    line(x + 18, y + 17, x + 25, y + 9, (138, 77, 22), 2)
    rect(x + 4, y + 24, s - 8, 18, FG)
    rect(x + 12, y + 29, s - 24, 3, (138, 77, 22))
    poly([(x + s - 12, y + 2), (x + s - 5, y + 2), (x + s - 10, y + 12),
          (x + s - 6, y + 12), (x + s - 13, y + 22), (x + s - 11, y + 13),
          (x + s - 15, y + 13)], GOLD)


def pic_crescent(x, y, s):
    circle(x + 18, y + 18, 12, GOLD)
    circle(x + 23, y + 14, 10, (92, 85, 75))
    rect(x + 4, y + s - 14, 10, 14, FG)
    rect(x + 17, y + s - 20, 12, 20, FG)
    rect(x + 32, y + s - 11, 9, 11, FG)


def pic_rugby(x, y, s):
    import math
    pts = []
    for i in range(25):
        a = 2 * math.pi * i / 24
        pts.append((x + s / 2 + 15 * math.cos(a), y + s / 2 + 14 * math.sin(a)))
    poly(pts, FG)
    line(x + s // 2 - 6, y + s // 2, x + s // 2 + 6, y + s // 2, (31, 81, 48), 2)
    for i in (-4, 0, 4):
        line(x + s // 2 + i, y + s // 2 - 3, x + s // 2 + i, y + s // 2 + 3,
             (31, 81, 48), 1)


def pic_chip(x, y, s):
    rect(x + 12, y + 10, s - 24, s - 20, FG)
    rect(x + 20, y + 17, s - 40, s - 34, (75, 46, 107))
    for i in range(3):
        rect(x + 4, y + 14 + i * 10, 8, 3, GOLD)
        rect(x + s - 12, y + 14 + i * 10, 8, 3, GOLD)
        rect(x + 16 + i * 10, y + 3, 3, 7, GOLD)
        rect(x + 16 + i * 10, y + s - 10, 3, 7, GOLD)


def pic_ship(x, y, s):
    poly([(x + 4, y + s - 16), (x + s - 4, y + s - 16),
          (x + s - 10, y + s - 6), (x + 10, y + s - 6)], FG)
    rect(x + 12, y + s - 26, 14, 9, GOLD)
    rect(x + 28, y + s - 26, 14, 9, (220, 120, 60))
    rect(x + 20, y + s - 35, 14, 9, (110, 170, 220))
    for i in range(3):
        rect(x + 6 + i * 15, y + s - 3, 9, 2, (160, 210, 235))


def pic_mountain(x, y, s):
    tri(x + 2, y + s - 8, x + 22, y + 6, x + 40, y + s - 8, FG)
    tri(x + 24, y + s - 8, x + 38, y + 14, x + s - 2, y + s - 8, FG)
    tri(x + 18, y + 13, x + 22, y + 6, x + 26, y + 13, (51, 86, 107))
    for i in range(3):
        rect(x + 5 + i * 14, y + s - 5, 9, 2, (160, 210, 235))


PICS = {
    "scales": pic_scales, "syringe": pic_syringe, "plane": pic_plane,
    "bank": pic_bank, "ballot": pic_ballot, "crescent": pic_crescent,
    "rugby": pic_rugby, "chip": pic_chip, "ship": pic_ship,
    "mountain": pic_mountain,
}


# ---------------------------------------------------------------- sections
MX = 18          # page margin
CW = W - 2 * MX  # content width = 988


def badge(x_right, y, label):
    bw = text_w(label, "sansb", 10) + 12
    rect(x_right - bw, y, bw, 15, BADGE_COLORS[label])
    text(x_right - bw + 6, y + 2, label, "sansb", 10, WHITE)
    return bw


def masthead():
    rect(0, 0, W, H, PAPER)
    text_c(W // 2, 14, "THE WORLD IN ONE PICTURE - MAKE.FUN DAILY",
           "sansb", 13, RED, tracking=3)
    text_c(W // 2, 36, "TUESDAY 24 NOVEMBER 2026", "serifb", 58, INK)
    rect(MX, 108, CW, 3, INK)
    rect(MX, 114, CW, 1, INK)
    text_c(W // 2, 122,
           "36 STORIES - 6 CONTINENTS + ORBIT - 13 PICTURED - "
           "EVERY STORY FROM THIS ONE DAY", "sansb", 12, NAVY)


def timeline_band():
    y = 140
    rect(0, y, W, 26, NAVY)
    text(MX, y + 7, "THE DAY IN UTC", "sansb", 11, GOLD)
    text(158, y + 8, TIMELINE, "sans", 10, WHITE)


def lead_panel(idx, x, y, story):
    num, region, bdg, head, sub = story
    w, h = 322, 264
    rect(x, y, w, h, CARD)
    rect_line(x, y, w, h, INK, 1)
    rect(x, y, w, 5, REGION_COLORS[region])
    illus = (pic_warship, pic_globe, pic_rocket)[idx]
    illus(x + 8, y + 13, w - 16, 118)
    text(x + 8, y + 140, "No.%d" % num, "sansb", 12, REGION_COLORS[region])
    text(x + 56, y + 141, region, "sansb", 10, GRAY)
    badge(x + w - 8, y + 139, bdg)
    block(x + 8, y + 160, head, "serifb", 20, INK, w - 16, 25, 2)
    block(x + 8, y + 214, sub, "serif", 12, (52, 60, 68), w - 16, 16, 3)


def medium_card(x, y, story):
    num, region, bdg, head, sub, big, bg, pic = story
    w, h = 189, 130
    rect(x, y, w, h, CARD)
    rect_line(x, y, w, h, INK, 1)
    rect(x, y, w, 4, REGION_COLORS[region])
    rect(x + 6, y + 8, w - 12, 44, bg)
    PICS[pic](x + 10, y + 10, 40)
    text_r(x + w - 12, y + 22, big, "serifb", 15, WHITE)
    text(x + 6, y + 58, "No.%d" % num, "sansb", 10, REGION_COLORS[region])
    text(x + 44, y + 58, region, "sansb", 10, GRAY)
    badge(x + w - 6, y + 57, bdg)
    block(x + 6, y + 74, head, "serifb", 13, INK, w - 12, 16, 2)
    block(x + 6, y + 104, sub, "sans", 10, (52, 60, 68), w - 12, 12, 2)


def map_box(y):
    x, w = MX, 618
    rect(x, y, w, 132, CARD)
    rect_line(x, y, w, 132, INK, 1)
    text(x + 10, y + 8, "WHERE IT HAPPENED - pins match story numbers",
         "sansb", 11, NAVY)
    dx0, dy0 = x + 14, y + 30
    dw, dh = w - 28, 92
    for row, spans in LAND_SPANS.items():
        for c0, c1 in spans:
            for c in range(c0, c1 + 1):
                rect(int(dx0 + c * dw / 72), int(dy0 + row * dh / 25), 5, 3,
                     (140, 158, 175))
    for num, (lon, lat) in PINS.items():
        px = int(dx0 + (lon + 180) / 360 * dw)
        py = int(dy0 + (85 - lat) / 145 * dh)
        circle(px, py, 8, WHITE)
        circle(px, py, 7, RED)
        s = str(num)
        text(px - text_w(s, "sansb", 10) // 2, py - 6, s, "sansb", 10, WHITE)


def date_check_box(y):
    x, w = 648, W - MX - 648
    rect(x, y, w, 132, (252, 244, 232))
    rect_line(x, y, w, 132, RED, 1)
    text(x + 10, y + 8, "DATE CHECK - LEFT OUT (OTHER DAYS)",
         "sansb", 11, RED)
    yy = y + 26
    for item in DATE_CHECK:
        text(x + 10, yy, "x", "sansb", 10, RED)
        n = block(x + 24, yy, item, "sans", 10, INK, w - 34, 12, 2)
        yy += 12 * max(1, n) + 1


def also_section(y):
    text(MX, y, "ALSO ON TUESDAY", "sansb", 12, NAVY)
    rect(MX + 168, y + 5, CW - 168, 1, GRAY)
    cols = [ALSO[i:i + 8] for i in range(0, len(ALSO), 8)]
    for ci, col in enumerate(cols):
        cx = MX + ci * 338
        for ri, (num, item) in enumerate(col):
            yy = y + 20 + ri * 12
            text(cx, yy, "%d" % num, "sansb", 10, RED)
            text(cx + 24, yy, item, "sans", 10, INK)


def footer(y):
    rect(MX, y, CW, 1, INK)
    text_c(W // 2, y + 5,
           "Sources: Reuters - PINA - C54 - Careerindia - Access24 - agency "
           "reports, all dated Tue 24 Nov 2026   * = scheduled at press time",
           "sans", 10, GRAY)
    text(MX, y + 19,
         "BADGES: CONFIRMED = 2+ outlets - OFFICIAL = on the record - "
         "REPORTED = one outlet", "sans", 10, GRAY)
    text_r(W - MX, y + 19, "Original drawings, drawn in code - @quick-raven-30",
           "sans", 10, GRAY)


def check_story_counts():
    pictured = len(LEADS) + len(MEDIUMS)
    assert pictured == 13, "expected 13 pictured stories, got %d" % pictured
    total = pictured + len(ALSO)
    assert total == 36, "expected 36 total stories, got %d" % total


def draw_page():
    masthead()
    timeline_band()
    for i, story in enumerate(LEADS):
        lead_panel(i, MX + i * 338, 176, story)
    for i, story in enumerate(MEDIUMS):
        medium_card(MX + (i % 5) * 199, 452 + (i // 5) * 140, story)
    map_box(730)
    date_check_box(730)
    also_section(874)
    footer(990)


def main():
    check_story_counts()
    draw_page()
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(out_dir, exist_ok=True)
    save_png(os.path.join(out_dir, "entry.png"))


if __name__ == "__main__":
    main()
