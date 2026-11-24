"""Front-page rasteriser for the 24 November 2026 world-news image.

Draws a 1024x1024 newspaper-style page: a masthead naming the day
and six story cards, each with a hand-drawn pictogram, a headline
and a short summary. Pure Python standard library, no photos, no
network, no disk fonts -- the glyphs are a hand-built 5x7 bitmap
font written in this file. Output is deterministic: the same input
always produces the same PNG bytes.
"""

import struct
import zlib

W, H = 1024, 1024

# --- palette -----------------------------------------------------------
NAVY = (13, 27, 46)        # page background
MAST = (19, 43, 74)        # masthead band
GOLD = (212, 175, 55)      # rules and masthead accents
PAPER = (244, 241, 232)    # story card background
INK = (22, 26, 34)         # headline/body ink
GREY = (96, 102, 116)      # secondary text
WHITE = (255, 255, 255)
SKY = (150, 198, 232)      # pictogram sky

# --- 5x7 bitmap font ---------------------------------------------------
# Each glyph is 7 rows of 5 cells; '#' is ink, '.' is clear.
GLYPHS = {
    'A': (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    'B': ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    'C': (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    'D': ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    'E': ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    'F': ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    'G': (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    'H': ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    'I': ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    'J': ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    'K': ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    'L': ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    'M': ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
}
GLYPHS.update({
    'N': ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    'O': (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    'P': ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    'Q': (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    'R': ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    'S': (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    'T': ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    'U': ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    'V': ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    'W': ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    'X': ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    'Y': ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    'Z': ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    '0': (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    '1': ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    '2': (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    '3': ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    '4': ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    '5': ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    '6': (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    '7': ("#####", "....#", "...#.", "...#.", "..#..", "..#..", "..#.."),
    '8': (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    '9': (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    ' ': (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    '.': (".....", ".....", ".....", ".....", ".....", ".....", "..#.."),
    ',': (".....", ".....", ".....", ".....", ".....", "..#..", ".#..."),
    ':': (".....", "..#..", ".....", "..#..", ".....", "..#..", "....."),
    ';': (".....", "..#..", ".....", "..#..", ".....", "..#..", ".#..."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    '-': (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    '%': ("#...#", "#..#.", "...#.", "..#..", ".#...", ".#..#", "#...#"),
    '+': (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    '/': ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    '(': ("...##", "..#..", ".#...", ".#...", ".#...", "..#..", "...##"),
    ')': ("##...", "..#..", "...#.", "...#.", "...#.", "..#..", "##..."),
    '&': (".###.", "#...#", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    '!': ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    '?': (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    '=': (".....", ".....", "#####", ".....", "#####", ".....", "....."),
})

CHAR_W = 6  # glyph pitch in font units (5 + 1 spacing)
CHAR_H = 7


def text_width(text, scale):
    """Pixel width of text at the given integer scale."""
    return len(text) * CHAR_W * scale


def wrap_words(text, max_px, scale):
    """Greedy word wrap; returns a list of lines fitting max_px."""
    lines, cur = [], ""
    for word in text.split(" "):
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_px or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines

# --- framebuffer ---------------------------------------------------------
class Canvas:
    """An RGB framebuffer with small filled-shape primitives."""

    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(w * h * 3)
        self.fill_rect(0, 0, w, h, bg)

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = c

    def fill_rect(self, x, y, w, h, c):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.px[i], self.px[i + 1], self.px[i + 2] = c

    def hline(self, x0, x1, y, c):
        if x1 < x0:
            x0, x1 = x1, x0
        for xx in range(max(0, x0), min(self.w, x1 + 1)):
            self.set(xx, y, c)

    def line(self, x0, y0, x1, y1, c):
        """Bresenham line."""
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.set(x0, y0, c)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, c):
        """Filled circle."""
        for yy in range(cy - r, cy + r + 1):
            half = int((r * r - (yy - cy) ** 2) ** 0.5) if abs(yy - cy) <= r else 0
            self.hline(cx - half, cx + half, yy, c)

    def ring(self, cx, cy, r, c, thick=3):
        for k in range(thick):
            rr = r - k
            for a in range(360):
                import math
                x = cx + int(rr * math.cos(math.radians(a)))
                y = cy + int(rr * math.sin(math.radians(a)))
                self.set(x, y, c)

    def poly(self, pts, c):
        """Scanline fill of a convex polygon given as [(x, y), ...]."""
        ys = [p[1] for p in pts]
        for yy in range(max(0, min(ys)), min(self.h, max(ys) + 1)):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= yy < y1) or (y1 <= yy < y0):
                    t = (yy - y0) / (y1 - y0)
                    xs.append(x0 + t * (x1 - x0))
            if len(xs) >= 2:
                self.hline(int(min(xs)), int(max(xs)), yy, c)

    def draw_text(self, x, y, text, scale, c):
        """Draw text with the bitmap font; unknown chars become spaces."""
        cx = x
        for ch in text:
            glyph = GLYPHS.get(ch, GLYPHS[' '])
            for row, bits in enumerate(glyph):
                for col, bit in enumerate(bits):
                    if bit == '#':
                        self.fill_rect(cx + col * scale, y + row * scale,
                                       scale, scale, c)
            cx += CHAR_W * scale
        return cx

    def text_centred(self, y, text, scale, c):
        x = (self.w - text_width(text, scale)) // 2
        self.draw_text(x, y, text, scale, c)


# --- PNG encoder ---------------------------------------------------------
def encode_png(canvas):
    raw = bytearray()
    stride = canvas.w * 3
    for yy in range(canvas.h):
        raw.append(0)  # filter: none
        raw += canvas.px[yy * stride:(yy + 1) * stride]

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        return out + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))

# --- pictograms ----------------------------------------------------------
# Each draws a small scene inside a square box (x, y, size).

def pic_chip(cv, x, y, s, accent):
    cx, cy = x + s // 2, y + s // 2
    cv.disc(cx, cy, s // 2 - 4, accent)
    body = s // 2
    bx, by = cx - body // 2, cy - body // 2
    cv.fill_rect(bx, by, body, body, INK)
    for k in range(3):  # pins on all four sides
        off_y = by + 8 + k * 14
        off_x = bx + 8 + k * 14
        cv.fill_rect(bx - 8, off_y, 8, 6, INK)
        cv.fill_rect(bx + body, off_y, 8, 6, INK)
        cv.fill_rect(off_x, by - 8, 6, 8, INK)
        cv.fill_rect(off_x, by + body, 6, 8, INK)
    cv.fill_rect(bx + 10, by + 10, body - 20, body - 20, accent)
    cv.fill_rect(bx + 18, by + 18, body - 36, body - 36, WHITE)


def pic_ship(cv, x, y, s, accent):
    cx, cy = x + s // 2, y + s // 2
    cv.disc(cx, cy, s // 2 - 4, SKY)
    cv.poly([(cx - 34, cy + 6), (cx + 34, cy + 6), (cx + 24, cy + 26),
             (cx - 24, cy + 26)], INK)          # hull
    cv.fill_rect(cx - 6, cy - 26, 4, 32, INK)    # mast
    cv.poly([(cx - 2, cy - 26), (cx + 22, cy - 18), (cx - 2, cy - 10)], accent)
    cv.hline(cx - 40, cx + 40, cy + 32, WHITE)   # waves
    cv.hline(cx - 30, cx + 30, cy + 38, WHITE)
    cv.fill_rect(cx - 26, cy - 8, 52, 6, WHITE)  # deck line


def pic_globe(cv, x, y, s, accent):
    cx, cy = x + s // 2, y + s // 2
    cv.disc(cx, cy, s // 2 - 4, accent)
    cv.disc(cx, cy, s // 2 - 12, (46, 139, 87))
    cv.hline(cx - 30, cx + 30, cy - 8, WHITE)   # latitude
    cv.hline(cx - 34, cx + 34, cy + 10, WHITE)
    cv.line(cx - 12, cy - 34, cx - 12, cy + 34, WHITE)  # meridian
    cv.line(cx + 12, cy - 34, cx + 12, cy + 34, WHITE)
    cv.poly([(cx + 6, cy - 30), (cx + 30, cy - 30), (cx + 6, cy - 6)], GOLD)


def pic_tanker(cv, x, y, s, accent):
    cx, cy = x + s // 2, y + s // 2
    cv.disc(cx, cy, s // 2 - 4, SKY)
    cv.fill_rect(cx - 36, cy - 2, 66, 22, INK)   # hull
    cv.fill_rect(cx - 28, cy - 16, 18, 14, INK)  # deck house
    cv.fill_rect(cx + 2, cy - 22, 14, 20, accent)  # funnel
    cv.hline(cx - 42, cx + 42, cy + 28, WHITE)   # water
    cv.hline(cx - 32, cx + 32, cy + 34, WHITE)
    # naval mine, top right
    mx, my = cx + 26, cy - 24
    cv.disc(mx, my, 9, INK)
    for dx, dy in ((0, -13), (0, 13), (-13, 0), (13, 0),
                   (-9, -9), (9, -9), (-9, 9), (9, 9)):
        cv.line(mx, my, mx + dx, my + dy, INK)


def pic_satellite(cv, x, y, s, accent):
    cx, cy = x + s // 2, y + s // 2
    cv.disc(cx, cy, s // 2 - 4, (24, 32, 56))
    cv.fill_rect(cx - 34, cy - 8, 22, 16, accent)   # left panel
    cv.fill_rect(cx + 12, cy - 8, 22, 16, accent)   # right panel
    cv.fill_rect(cx - 12, cy - 12, 24, 24, GOLD)    # body
    cv.fill_rect(cx - 5, cy - 5, 10, 10, INK)
    cv.line(cx, cy - 12, cx + 16, cy - 30, WHITE)   # antenna
    cv.disc(cx + 18, cy - 32, 3, WHITE)
    cv.disc(cx + 26, cy - 36, 2, WHITE)


def pic_flame(cv, x, y, s, accent):
    cx, cy = x + s // 2, y + s // 2
    cv.disc(cx, cy, s // 2 - 4, (40, 26, 20))
    cv.poly([(cx - 22, cy + 28), (cx - 6, cy - 6), (cx + 2, cy + 8),
             (cx + 12, cy - 30), (cx + 24, cy + 28)], accent)  # outer flame
    cv.poly([(cx - 10, cy + 28), (cx - 2, cy + 6), (cx + 4, cy + 16),
             (cx + 10, cy - 8), (cx + 12, cy + 28)], GOLD)     # inner flame


# --- the six stories of 24 November 2026 --------------------------------
STORIES = [
    dict(kicker="TECH - USA", accent=(118, 185, 0), pic=pic_chip,
         headline="HUANG BACK AT NVIDIA",
         body="Board reinstates Jensen Huang as chief executive. "
              "Shares jump 31% in a day, the largest one-day gain ever."),
    dict(kicker="CONFLICT - LIBYA", accent=(58, 110, 165), pic=pic_ship,
         headline="UKRAINE SINKS RUSSIAN WARSHIP",
         body="Kyiv says seven naval drones sank the corvette Merkury "
              "at Benghazi, Libya, carrying the war to the Med."),
    dict(kicker="CLIMATE - TURKEY", accent=(46, 139, 87), pic=pic_globe,
         headline="COP31 ENDS WITH NO DEAL",
         body="Talks in Antalya collapse after 50 hours of overtime. "
              "Over 90 nations reject a text silent on fossil fuels."),
    dict(kicker="ENERGY - GULF", accent=(214, 110, 0), pic=pic_tanker,
         headline="MINES HIT TANKERS IN HORMUZ",
         body="Three tankers strike naval mines in the Strait of Hormuz, "
              "Iran says, as Gulf tensions and oil fears rise."),
    dict(kicker="SECURITY - SPACE", accent=(98, 80, 180), pic=pic_satellite,
         headline="NATO WARNS ON SPACE THREAT",
         body="NATO vows to defend space after reports Russia may put a "
              "nuclear weapon in orbit within 60 days."),
    dict(kicker="DISASTER - INDONESIA", accent=(178, 34, 34), pic=pic_flame,
         headline="FACTORY FIRE KILLS 26",
         body="A fire at a factory in Banten, Indonesia, kills 26 workers. "
              "Dozens are still missing as rescuers search the site."),
]

# --- page layout -----------------------------------------------------------
def render_card(cv, x, y, w, h, story):
    cv.fill_rect(x, y, w, h, PAPER)
    cv.fill_rect(x, y, w, 10, story["accent"])          # accent strip
    pad = 18
    ix, iy, isize = x + pad, y + 26, 104
    story["pic"](cv, ix, iy, isize, story["accent"])
    tx = x + pad + isize + 16
    tw = x + w - pad - tx
    cv.draw_text(tx, y + 30, story["kicker"], 2, story["accent"])
    head_lines = wrap_words(story["headline"], tw, 2)
    hy = y + 58
    for line in head_lines[:2]:
        cv.draw_text(tx, hy, line, 2, INK)
        hy += 20
    body_lines = wrap_words(story["body"].upper(), w - 2 * pad, 2)
    by = y + 26 + isize + 14
    for line in body_lines[:3]:
        cv.draw_text(x + pad, by, line, 2, INK)
        by += 20


def render():
    cv = Canvas(W, H, NAVY)
    # masthead
    cv.fill_rect(0, 0, W, 148, MAST)
    cv.fill_rect(0, 148, W, 4, GOLD)
    cv.text_centred(22, "THE WORLD TODAY", 5, WHITE)
    cv.text_centred(72, "TUESDAY 24 NOVEMBER 2026", 3, GOLD)
    cv.text_centred(108, "SIX STORIES FROM AROUND THE GLOBE", 2, (190, 200, 215))
    # story grid: 2 columns x 3 rows
    gx, gy = 8, 164
    cw, chh, gap = 496, 260, 16
    for i, story in enumerate(STORIES):
        cx = gx + (i % 2) * (cw + gap)
        cy = gy + (i // 2) * (chh + gap)
        render_card(cv, cx, cy, cw, chh, story)
    # footer
    cv.fill_rect(0, 984, W, 4, GOLD)
    cv.text_centred(998, "EVENTS REPORTED ON TUESDAY 24 NOVEMBER 2026", 2, (190, 200, 215))
    return cv


if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "entry.png"
    data = encode_png(render())
    with open(out, "wb") as f:
        f.write(data)
    print("wrote", out, len(data), "bytes")
