#!/usr/bin/env python3
"""Authoring-time renderer for one page of the world's news on 19 November 2026.

Layout, top to bottom:
    strapline and folio          what this is, and how much of the day is on it
    masthead                     the date, the largest thing on the page
    figure rail                  six numerals, six different stories
    three lead cards             art panel, kicker, headline, deck
    eight brief cards            icon, kicker, headline, deck
    map and key                  where each of the eleven numbered stories happened
    agate index                  the rest of the day, one line each
    sources line

Nothing here ships with the entry: `main.py` only copies the finished `entry.png` to
`/output/entry.png`. This script runs at authoring time, where Pillow is available.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import content  # noqa: E402

S = 2                      # supersample factor
W = 1024
M = 20                     # outer margin
CW = W - 2 * M             # content width, 984

PAPER = (247, 244, 236)
INK = (26, 24, 22)
MUTED = (92, 87, 79)
ACCENT = (170, 32, 36)     # the page's only accent, spent on information
RULE = (198, 191, 177)
WASH = (232, 227, 214)
WHITE = (255, 255, 255)

FACES = {
    "serif": "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
    "sans": "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "sansb": "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
}

image = Image.new("RGB", (W * S, W * S), PAPER)
draw = ImageDraw.Draw(image)
_fonts: dict[tuple[int, str], ImageFont.FreeTypeFont] = {}
_cells: list[dict] = []
_rules: list[tuple[float, float, float]] = []
_placed: list[dict] = []
_issues: list[str] = []


# ---------------------------------------------------------------- primitives

def font(size: float, face: str) -> ImageFont.FreeTypeFont:
    key = (max(1, int(round(size * S))), face)
    if key not in _fonts:
        _fonts[key] = ImageFont.truetype(FACES[face], key[0])
    return _fonts[key]


def P(v: float) -> int:
    return int(round(v * S))


def tw(text: str, size: float, face: str = "sans", tracking: float = 0.0) -> float:
    """Width of `text` in page units, tracking included."""
    f = font(size, face)
    w = draw.textlength(text, font=f) / S
    if tracking:
        w += tracking * max(0, len(text) - 1)
    return w


def caps(text: str, size: float, face: str, x: float, y: float, color=INK,
         tracking: float = 1.1, align: str = "left", limit: float | None = None,
         cell: str = "", name: str = "") -> float:
    """Letterspaced text, y is the top of the line box."""
    f = font(size, face)
    width = tw(text, size, face, tracking)
    if align == "right":
        x = x - width
    elif align == "center":
        x = x - width / 2
    if limit is not None and width > limit + 0.5:
        _issues.append(f"{cell}/{name}: {text[:32]!r} is {width:.1f} wide, limit {limit:.1f}")
    cx = x
    for ch in text:
        draw.text((P(cx), P(y)), ch, font=f, fill=color)
        cx += draw.textlength(ch, font=f) / S + tracking
    _placed.append({"cell": cell, "name": name, "x": round(x, 1), "y": round(y, 1),
                    "w": round(width, 1), "h": round(size, 1), "text": text[:60]})
    return width


def text(x: float, y: float, s: str, size: float, face: str = "sans", color=INK,
         align: str = "left", limit: float | None = None, cell: str = "") -> float:
    f = font(size, face)
    width = draw.textlength(s, font=f) / S
    if align == "right":
        x = x - width
    elif align == "center":
        x = x - width / 2
    if limit is not None and width > limit + 0.5:
        _issues.append(f"{cell}: {s[:40]!r} is {width:.1f} wide, limit {limit:.1f}")
    draw.text((P(x), P(y)), s, font=f, fill=color)
    _placed.append({"cell": cell, "name": s[:24], "x": round(x, 1), "y": round(y, 1),
                    "w": round(width, 1), "h": round(size, 1), "text": s[:60]})
    return width


def wrap(s: str, size: float, face: str, width: float) -> list[str]:
    f = font(size, face)
    out, line = [], ""
    for word in s.split():
        trial = word if not line else line + " " + word
        if draw.textlength(trial, font=f) / S <= width or not line:
            line = trial
        else:
            out.append(line)
            line = word
    if line:
        out.append(line)
    return out


def para(x: float, y: float, s: str, size: float, face: str, width: float,
         leading: float, max_lines: int, color=INK, cell: str = "", name: str = "") -> float:
    """Wrap and draw; returns the y after the last line. Height is checked, not clipped."""
    lines = wrap(s, size, face, width)
    if len(lines) > max_lines:
        _issues.append(f"{cell}/{name}: needs {len(lines)} lines at {size}px, only {max_lines} fit")
        lines = lines[:max_lines]
    f = font(size, face)
    for i, ln in enumerate(lines):
        draw.text((P(x), P(y + i * leading)), ln, font=f, fill=color)
        _placed.append({"cell": cell, "name": name, "x": round(x, 1), "y": round(y + i * leading, 1),
                        "w": round(draw.textlength(ln, font=f) / S, 1), "h": round(size, 1),
                        "text": ln[:60]})
    return y + len(lines) * leading


def hair(x0: float, y: float, x1: float, color=RULE, width: float = 1.0) -> None:
    _rules.append((y, x0, x1))
    draw.line([(P(x0), P(y)), (P(x1), P(y))], fill=color, width=max(1, P(width)))


def vhair(x: float, y0: float, y1: float, color=RULE, width: float = 1.0) -> None:
    draw.line([(P(x), P(y0)), (P(x), P(y1))], fill=color, width=max(1, P(width)))


def box(x0: float, y0: float, x1: float, y1: float, fill=None, outline=None, width: float = 1.0) -> None:
    draw.rectangle([P(x0), P(y0), P(x1) - 1, P(y1) - 1], fill=fill,
                   outline=outline, width=max(1, P(width)))


def cell(name: str, x0: float, y0: float, x1: float, y1: float) -> None:
    _cells.append({"name": name, "box": [round(v, 1) for v in (x0, y0, x1, y1)]})


# ------------------------------------------------------------------ drawing

def poly(pts, fill=None, outline=None, width: float = 1.4) -> None:
    draw.polygon([(P(x), P(y)) for x, y in pts], fill=fill,
                 outline=outline, width=max(1, P(width)))


def stroke(pts, color=INK, width: float = 1.6, joint: str = "curve") -> None:
    draw.line([(P(x), P(y)) for x, y in pts], fill=color, width=max(1, P(width)), joint=joint)


def circ(cx: float, cy: float, r: float, fill=None, outline=None, width: float = 1.4) -> None:
    draw.ellipse([P(cx - r), P(cy - r), P(cx + r), P(cy + r)], fill=fill,
                 outline=outline, width=max(1, P(width)))


def disc(cx: float, cy: float, r: float, fill=ACCENT, label: str = "", size: float = 10.0) -> None:
    circ(cx, cy, r, fill=fill)
    if label:
        f = font(size, "sansb")
        w = draw.textlength(label, font=f) / S
        draw.text((P(cx - w / 2), P(cy - size * 0.62)), label, font=f, fill=WHITE)


# --------------------------------------------------------------- hero art

def art_summit(x0, y0, x1, y1) -> None:
    """Three figures at one long table, hall arch behind, host city's skyline in the back."""
    w, h = x1 - x0, y1 - y0
    box(x0, y0, x1, y1, fill=WASH)
    # hall: a wide arch and a horizon of towers
    stroke([(x0 + w * 0.06, y0 + h * 0.62), (x0 + w * 0.06, y0 + h * 0.26),
            (x0 + w * 0.5, y0 + h * 0.10), (x0 + w * 0.94, y0 + h * 0.26),
            (x0 + w * 0.94, y0 + h * 0.62)], color=RULE, width=1.2)
    for i, bx in enumerate((0.14, 0.26, 0.38, 0.62, 0.74, 0.86)):
        bh = (0.10, 0.16, 0.08, 0.12, 0.19, 0.09)[i]
        box(x0 + w * bx, y0 + h * 0.62 - h * bh, x0 + w * (bx + 0.055), y0 + h * 0.62,
            fill=None, outline=RULE, width=1.0)
    hair(x0 + w * 0.04, y0 + h * 0.62, x1 - w * 0.04, color=RULE)
    # table
    box(x0 + w * 0.07, y0 + h * 0.80, x1 - w * 0.07, y0 + h * 0.88, fill=INK)
    stroke([(x0 + w * 0.13, y0 + h * 0.88), (x0 + w * 0.13, y0 + h * 0.96)], width=2.0)
    stroke([(x1 - w * 0.13, y0 + h * 0.88), (x1 - w * 0.13, y0 + h * 0.96)], width=2.0)
    # three figures behind the table: head, shoulders, nameplate
    for i, cx in enumerate((0.25, 0.5, 0.75)):
        r = h * (0.075, 0.082, 0.075)[i]
        head_y = y0 + h * (0.50, 0.47, 0.50)[i]
        circ(x0 + w * cx, head_y, r, fill=INK)
        stroke([(x0 + w * cx - r * 1.5, y0 + h * 0.79), (x0 + w * cx - r * 1.2, y0 + h * 0.66),
                (x0 + w * cx - r * 0.5, y0 + h * 0.60)], width=3.2)
        stroke([(x0 + w * cx + r * 1.5, y0 + h * 0.79), (x0 + w * cx + r * 1.2, y0 + h * 0.66),
                (x0 + w * cx + r * 0.5, y0 + h * 0.60)], width=3.2)
        stroke([(x0 + w * cx - r * 0.9, y0 + h * 0.60), (x0 + w * cx, y0 + h * 0.58),
                (x0 + w * cx + r * 0.9, y0 + h * 0.60)], width=3.2)
        box(x0 + w * cx - r * 1.1, y0 + h * 0.70, x0 + w * cx + r * 1.1, y0 + h * 0.735,
            fill=WHITE, outline=RULE, width=1.0)
    # three flags on the table's edge, tallest in the middle
    for i, cx in enumerate((0.25, 0.5, 0.75)):
        fx, fh = x0 + w * cx, h * (0.055, 0.065, 0.055)[i]
        stroke([(fx, y0 + h * 0.80), (fx, y0 + h * 0.80 - fh)], width=1.4)
        poly([(fx, y0 + h * 0.80 - fh), (fx + w * 0.035, y0 + h * 0.80 - fh + fh * 0.22),
              (fx, y0 + h * 0.80 - fh + fh * 0.44)], fill=ACCENT if i == 0 else INK)


def art_court(x0, y0, x1, y1) -> None:
    """A court: pediment, columns, steps — and the scales in front of them."""
    w, h = x1 - x0, y1 - y0
    box(x0, y0, x1, y1, fill=WASH)
    cx = x0 + w * 0.5
    # pediment
    poly([(cx - w * 0.34, y0 + h * 0.34), (cx, y0 + h * 0.13), (cx + w * 0.34, y0 + h * 0.34)],
         fill=None, outline=INK, width=2.0)
    poly([(cx - w * 0.22, y0 + h * 0.31), (cx, y0 + h * 0.20), (cx + w * 0.22, y0 + h * 0.31)],
         fill=RULE)
    box(cx - w * 0.36, y0 + h * 0.34, cx + w * 0.36, y0 + h * 0.385, fill=INK)
    # columns
    for i in range(6):
        bx = cx - w * 0.30 + i * (w * 0.60 / 5.0)
        box(bx - w * 0.022, y0 + h * 0.385, bx + w * 0.022, y0 + h * 0.68, fill=WHITE,
            outline=INK, width=1.6)
        box(bx - w * 0.030, y0 + h * 0.375, bx + w * 0.030, y0 + h * 0.395, fill=INK)
    # steps
    for i in range(3):
        box(cx - w * (0.40 - i * 0.03), y0 + h * (0.68 + i * 0.045),
            cx + w * (0.40 - i * 0.03), y0 + h * (0.715 + i * 0.045), fill=WHITE,
            outline=INK, width=1.4)
    # the scales, hung in front of the portico
    top = y0 + h * 0.855
    stroke([(cx, y0 + h * 0.44), (cx, top)], width=2.2)
    stroke([(cx - w * 0.15, y0 + h * 0.475), (cx + w * 0.15, y0 + h * 0.475)], width=2.2)
    for sx in (cx - w * 0.15, cx + w * 0.15):
        stroke([(sx, y0 + h * 0.475), (sx, y0 + h * 0.545)], width=1.2)
        draw.arc([P(sx - w * 0.055), P(y0 + h * 0.505), P(sx + w * 0.055), P(y0 + h * 0.585)],
                 start=0, end=180, fill=ACCENT, width=max(1, P(2.2)))
    box(cx - w * 0.05, top - h * 0.02, cx + w * 0.05, top + h * 0.012, fill=INK)


def art_markets(x0, y0, x1, y1) -> None:
    """A listing: bars stepping up, an arrow over them, a ticker rule beneath."""
    w, h = x1 - x0, y1 - y0
    box(x0, y0, x1, y1, fill=WASH)
    base = y0 + h * 0.74
    hair(x0 + w * 0.06, base, x1 - w * 0.06, color=RULE)
    heights = (0.10, 0.16, 0.14, 0.24, 0.31, 0.30, 0.44, 0.56)
    for i, hh in enumerate(heights):
        bx = x0 + w * (0.09 + i * 0.105)
        box(bx, base - h * hh, bx + w * 0.062, base, fill=INK if i < 7 else ACCENT)
    # arrow over the run
    stroke([(x0 + w * 0.10, base - h * 0.18), (x0 + w * 0.34, base - h * 0.30),
            (x0 + w * 0.55, base - h * 0.44), (x0 + w * 0.80, base - h * 0.66)],
           color=ACCENT, width=2.4)
    poly([(x0 + w * 0.80, base - h * 0.66), (x0 + w * 0.72, base - h * 0.60),
          (x0 + w * 0.78, base - h * 0.54)], fill=ACCENT)
    # a ticker tape along the foot of the panel
    for i in range(9):
        bx = x0 + w * (0.06 + i * 0.10)
        box(bx, y0 + h * 0.84, bx + w * 0.055, y0 + h * 0.88, fill=RULE)


# ---------------------------------------------------------------- card icons

def icon(kind: str, x0: float, y0: float, size: float) -> None:
    """A 34 px schematic so the card reads as a picture even at thumbnail scale."""
    w = h = size
    cx, cy = x0 + w / 2, y0 + h / 2
    box(x0, y0, x0 + w, y0 + h, fill=WASH)
    if kind == "game":
        draw.rounded_rectangle([P(x0 + w * 0.08), P(y0 + h * 0.26), P(x0 + w * 0.92), P(y0 + h * 0.74)],
                               radius=P(5), outline=INK, width=max(1, P(1.8)))
        circ(cx - w * 0.20, cy, w * 0.07, fill=INK)
        circ(cx + w * 0.22, cy - h * 0.05, w * 0.10, fill=ACCENT)
    elif kind == "bridge":
        stroke([(x0 + w * 0.06, y0 + h * 0.60), (x0 + w * 0.44, y0 + h * 0.60)], width=2.6)
        stroke([(x0 + w * 0.56, y0 + h * 0.60), (x0 + w * 0.94, y0 + h * 0.60)], width=2.6)
        for tx in (0.22, 0.72):
            stroke([(x0 + w * tx, y0 + h * 0.22), (x0 + w * tx, y0 + h * 0.82)], width=2.2)
        stroke([(x0 + w * 0.44, y0 + h * 0.60), (x0 + w * 0.52, y0 + h * 0.74)], color=ACCENT, width=1.8)
        stroke([(x0 + w * 0.56, y0 + h * 0.60), (x0 + w * 0.48, y0 + h * 0.74)], color=ACCENT, width=1.8)
    elif kind == "missile":
        draw.arc([P(x0 + w * 0.05), P(y0 + h * 0.10), P(x0 + w * 1.05), P(y0 + h * 0.95)],
                 start=200, end=310, fill=ACCENT, width=max(1, P(2.0)))
        poly([(x0 + w * 0.74, y0 + h * 0.30), (x0 + w * 0.86, y0 + h * 0.16),
              (x0 + w * 0.82, y0 + h * 0.38)], fill=INK)
        stroke([(x0 + w * 0.82, y0 + h * 0.32), (x0 + w * 0.70, y0 + h * 0.44)], width=1.6)
    elif kind == "boat":
        poly([(x0 + w * 0.12, y0 + h * 0.52), (x0 + w * 0.88, y0 + h * 0.52),
              (x0 + w * 0.72, y0 + h * 0.70), (x0 + w * 0.28, y0 + h * 0.70)],
             fill=None, outline=INK, width=2.0)
        for i in range(3):
            stroke([(x0 + w * 0.20, y0 + h * 0.78), (x0 + w * 0.34, y0 + h * 0.82),
                    (x0 + w * 0.48, y0 + h * 0.78), (x0 + w * 0.62, y0 + h * 0.82),
                    (x0 + w * 0.78, y0 + h * 0.78)], color=ACCENT, width=1.4)
    elif kind == "tank":
        box(x0 + w * 0.14, y0 + h * 0.58, x0 + w * 0.86, y0 + h * 0.76, fill=INK)
        box(x0 + w * 0.30, y0 + h * 0.42, x0 + w * 0.66, y0 + h * 0.58, fill=None,
            outline=INK, width=2.0)
        stroke([(x0 + w * 0.66, y0 + h * 0.48), (x0 + w * 0.90, y0 + h * 0.42)],
               color=ACCENT, width=2.4)
        for gx in (0.24, 0.42, 0.60, 0.78):
            circ(x0 + w * gx, y0 + h * 0.78, w * 0.05, fill=INK)
    elif kind == "ice":
        poly([(x0 + w * 0.16, y0 + h * 0.62), (x0 + w * 0.46, y0 + h * 0.20),
              (x0 + w * 0.58, y0 + h * 0.44), (x0 + w * 0.70, y0 + h * 0.30),
              (x0 + w * 0.86, y0 + h * 0.62)], fill=WHITE, outline=INK, width=1.8)
        hair(x0 + w * 0.06, y0 + h * 0.62, x0 + w * 0.94, color=ACCENT, width=2.0)
        stroke([(x0 + w * 0.16, y0 + h * 0.72), (x0 + w * 0.34, y0 + h * 0.66)], color=RULE, width=1.2)
    elif kind == "mine":
        poly([(x0 + w * 0.20, y0 + h * 0.80), (x0 + w * 0.50, y0 + h * 0.22),
              (x0 + w * 0.80, y0 + h * 0.80)], fill=None, outline=INK, width=2.2)
        circ(x0 + w * 0.50, y0 + h * 0.22, w * 0.07, fill=ACCENT)
        hair(x0 + w * 0.20, y0 + h * 0.80, x0 + w * 0.80, color=INK, width=2.0)
    elif kind == "art":
        box(x0 + w * 0.14, y0 + h * 0.18, x0 + w * 0.86, y0 + h * 0.82, fill=WHITE,
            outline=INK, width=2.0)
        stroke([(x0 + w * 0.20, y0 + h * 0.74), (x0 + w * 0.40, y0 + h * 0.46),
                (x0 + w * 0.58, y0 + h * 0.74)], color=ACCENT, width=1.8)
        circ(x0 + w * 0.66, y0 + h * 0.36, w * 0.06, fill=ACCENT)


# --------------------------------------------------------------------- map

def map_xform(x0: float, y0: float, w: float, h: float):
    """Equal-area-ish equirectangular fit, letterboxed inside the box so nothing distorts."""
    lon_min, lon_max = -170.0, 186.0
    lat_min, lat_max = -50.0, 76.0
    scale = min(w / (lon_max - lon_min), h / (lat_max - lat_min))
    ox = x0 + (w - (lon_max - lon_min) * scale) / 2
    oy = y0 + (h - (lat_max - lat_min) * scale) / 2

    def proj(lon: float, lat: float) -> tuple[float, float]:
        return ox + (lon - lon_min) * scale, oy + (lat_max - lat) * scale

    return proj


def world_map(x0: float, y0: float, x1: float, y1: float):
    rings = json.loads((Path(__file__).resolve().parent / "data" / "land.json").read_text())
    w, h = x1 - x0, y1 - y0
    proj = map_xform(x0, y0, w, h)
    box(x0, y0, x1, y1, fill=(241, 238, 229))
    # graticule first, very faint
    for lat in (-40, -20, 0, 20, 40, 60):
        _, yy = proj(0, lat)
        hair(x0 + 1, yy, x1 - 1, color=(228, 223, 211), width=0.7)
    for lon in (-120, -60, 0, 60, 120):
        xx, _ = proj(lon, 0)
        vhair(xx, y0 + 1, y1 - 1, color=(228, 223, 211), width=0.7)
    _, eq = proj(0, 0)
    hair(x0 + 1, eq, x1 - 1, color=RULE, width=0.9)
    for ring in rings:
        pts = [proj(lon, lat) for lon, lat in ring]
        pts = [(x, y) for x, y in pts if x0 - 3 <= x <= x1 + 3 and y0 - 3 <= y <= y1 + 3]
        if len(pts) < 4:
            continue
        poly(pts, fill=(223, 216, 200), outline=(122, 115, 102), width=0.9)
    return proj


# Where each pin's numeral sits relative to its dot, in page pixels. Six of the
# eleven stories fall inside a 20 px square over western Europe, so a disc per story
# would bury the continent. Instead each story gets a dot at its true coordinate and
# a numeral called out beside it, the way an atlas labels a crowded coast.
PIN_LABELS = {
    1: (9, 1),     # Shenzhen, called out into the Pacific
    2: (9, 5),     # The Hague
    3: (9, 1),     # New York
    4: (-10, 3),   # Sydney
    5: (10, 2),    # Kerch
    6: (10, 1),    # Riyadh
    7: (-10, 1),   # Dakar, out over the Atlantic
    8: (-10, 7),   # Gaza, down towards Sinai
    9: (3, -10),   # Copenhagen, up into the North Sea
    10: (10, 1),   # Nairobi
    11: (-10, -8),  # London, out past Ireland
}


def pins(proj, rows, bounds) -> None:
    x0, y0, x1, y1 = bounds
    for story in rows:
        x, y = proj(story["pin"][0], story["pin"][1])
        x = min(max(x, x0 + 3), x1 - 3)
        y = min(max(y, y0 + 3), y1 - 3)
        dx, dy = PIN_LABELS[story["num"]]
        stroke([(x, y), (x + dx * 0.55, y + dy * 0.55)], color=ACCENT, width=0.9)
        circ(x, y, 2.1, fill=ACCENT)
        draw.text((P(x + dx), P(y + dy)), str(story["num"]), font=font(8.0, "sansb"),
                  fill=ACCENT, anchor="lm" if dx >= 0 else "rm",
                  stroke_width=max(1, P(0.6)), stroke_fill=PAPER)


# ----------------------------------------------------------------- sections

def header() -> None:
    caps("THE WORLD'S NEWS IN ONE PICTURE", 8.8, "sansb", M, 22, color=MUTED, tracking=1.6, cell="header")
    caps(f"{content.story_count()} STORIES \u00b7 SIX REGIONS \u00b7 ONE PAGE", 8.8, "sansb",
         W - M, 22, color=ACCENT, tracking=1.6, align="right", cell="header", name="count")
    hair(M, 35, W - M, color=INK, width=1.4)
    caps(content.NAME, 10.6, "sansb", M, 41, color=ACCENT, tracking=3.2, cell="header")

    # the date, sized to leave the standfirst a column of its own
    size, stand_w = 41.0, 322.0
    date_w = tw(content.DATE, size, "serif", 0.5) + 0.5 * (len(content.DATE) - 1)
    while date_w > CW - stand_w - 26 and size > 26:
        size -= 1
        date_w = tw(content.DATE, size, "serif", 0.5) + 0.5 * (len(content.DATE) - 1)
    caps(content.DATE, size, "serif", M, 56, color=INK, tracking=0.5, limit=CW, cell="header", name="date")
    para(W - M - stand_w, 54, "Everything here was reported, or first published, on Thursday. "
         f"{content.story_count()} stories from six regions, drawn in code on one sheet, "
         "so that the day can be read at a glance.",
         11.4, "sans", stand_w, 13.2, 5, color=INK, cell="header", name="standfirst")

    hair(M, 100, W - M, color=INK, width=2.4)
    hair(M, 104, W - M, color=RULE, width=0.8)
    caps("ALL THE NEWS OF ONE DAY, FROM SIX REGIONS AND EVERY FIELD", 8.8, "sansb",
         M, 110, color=MUTED, tracking=1.3, cell="header")
    caps("ILLUSTRATED AND DRAWN FOR THIS PAGE", 8.8, "sansb", W - M, 110, color=MUTED,
         tracking=1.3, align="right", cell="header")
    hair(M, 124, W - M, color=INK, width=1.2)


def figure_rail() -> None:
    top = 130
    cell_w = CW / len(content.FIGURES)
    for i, (value, label) in enumerate(content.FIGURES):
        x = M + i * cell_w
        cell(f"figure{i}", x, top, x + cell_w - 8, top + 56)
        if i:
            vhair(x - 6, top + 3, top + 50, color=RULE)
        w_val = text(x, top, value, 23, "serif", color=INK, limit=cell_w - 14, cell=f"figure{i}")
        box(x, top + 30, x + min(w_val, cell_w - 14), top + 31.8, fill=ACCENT)
        vy = top + 35
        for ln in wrap(label, 9.8, "sans", cell_w - 14)[:2]:
            text(x, vy, ln, 9.8, "sans", color=MUTED, cell=f"figure{i}")
            vy += 12.0
    hair(M, top + 62, W - M, color=RULE, width=0.9)


def lead() -> None:
    """One story carries the page: the largest headline, the only full-width art."""
    top, bottom = 198, 430
    art_x1 = M + 392
    art = {"summit": art_summit, "court": art_court, "markets": art_markets}[content.HEROES[0]["art"]]
    art(M, top, art_x1, bottom)
    cell("lead-art", M, top, art_x1, bottom)

    story = content.HEROES[0]
    disc(M + 15, top + 15, 10.4, fill=ACCENT, label=str(story["num"]), size=11.6)
    caps(story["place"].upper(), 9.2, "sansb", art_x1 - 9, top + 9, color=INK,
         tracking=1.3, align="right", limit=200, cell="lead-art", name="place")

    tx = art_x1 + 22
    tw_ = W - M - tx
    caps(f"LEAD \u00b7 {story['region']} \u00b7 {story['kicker']}", 11.8, "sansb", tx, top,
         color=ACCENT, tracking=1.7, limit=tw_, cell="lead", name="kicker")
    y = para(tx, top + 20, story["head"], 34.0, "serif", tw_, 38.5, 3, INK, "lead", "head")
    hair(tx, y + 9, W - M, color=INK, width=1.2)
    y = para(tx, y + 20, story["deck"], 13.6, "sans", tw_, 18.0, 3, INK, "lead", "deck")
    for line in (story.get("detail") or [])[:3]:
        y += 3
        circ(tx + 2.6, y + 5.2, 1.9, fill=ACCENT)
        y = para(tx + 13, y, line, 11.8, "sans", tw_ - 13, 14.4, 1, INK, "lead", "detail") - 1
    caps("THE DAY'S LEAD STORY \u2014 SEE PAGE ONE", 8.4, "sansb", tx, bottom - 14,
         color=MUTED, tracking=1.2, limit=tw_, cell="lead")


def second_leads() -> None:
    """Two more stories at half the lead's weight, still readable as headlines."""
    top, gap = 438, 16
    cw = (CW - gap) / 2
    art_h = 58
    for i, story in enumerate(content.HEROES[1:]):
        x = M + i * (cw + gap)
        cell(f"hero{i}", x, top, x + cw, top + 152)
        art = {"summit": art_summit, "court": art_court, "markets": art_markets}[story["art"]]
        art(x, top, x + cw, top + art_h)
        disc(x + 11, top + 11, 8.0, fill=ACCENT, label=str(story["num"]), size=9.2)
        caps(story["place"].upper(), 7.6, "sansb", x + cw - 8, top + 5, color=INK,
             tracking=1.2, align="right", limit=cw - 30, cell=f"hero{i}", name="place")
        y = top + art_h + 6
        caps(f"{story['num']:02d} \u00b7 {story['kicker']}", 9.0, "sansb", x, y, color=ACCENT,
             tracking=1.3, limit=cw, cell=f"hero{i}", name="kicker")
        y = para(x, y + 11, story["head"], 17.8, "serif", cw, 21.0, 3, INK, f"hero{i}", "head")
        para(x, y + 5, story["deck"], 10.4, "sans", cw, 12.8, 2, MUTED, f"hero{i}", "deck")


def brief_cards() -> None:
    top, gap = 598, 11
    cw = (CW - 3 * gap) / 4
    ch = 82
    for i, story in enumerate(content.SECONDARY):
        col, row = i % 4, i // 4
        x = M + col * (cw + gap)
        y = top + row * (ch + 12)
        cell(f"brief{i}", x, y, x + cw, y + ch)
        icon(story["icon"], x, y, 30)
        tx = x + 30 + 8
        tw_ = cw - 30 - 8
        caps(f"{story['num']:02d} \u00b7 {story['kicker']}", 7.8, "sansb", tx, y - 0.5,
             color=ACCENT, tracking=0.9, limit=tw_, cell=f"brief{i}", name="kicker")
        para(tx, y + 10, story["head"], 12.8, "sansb", tw_, 14.8, 3, INK, f"brief{i}", "head")
        para(tx, y + 57.2, story["deck"], 9.4, "sans", tw_, 11.4, 2, MUTED, f"brief{i}", "deck")


def map_band() -> None:
    top = 782
    rows = content.HEROES + content.SECONDARY
    caps("WHERE IT HAPPENED", 10.0, "sansb", M, top, color=INK, tracking=2.4, cell="map")
    caps(f"{len(rows)} OF THE {content.story_count()} STORIES, PINNED TO THE MAP",
         8.6, "sansb", 494, top + 1.8, color=MUTED, tracking=1.3, align="right", limit=380, cell="map")
    hair(M, top + 14, 494, color=INK, width=1.2)
    mx0, my0, mx1, my1 = M, top + 18, 494, top + 92
    proj = world_map(mx0, my0, mx1, my1)
    pins(proj, rows, (mx0, my0, mx1, my1))

    # how much of the whole day each region carries, on the page and on the map
    counts: dict[str, int] = {}
    for story in rows:
        counts[story["region"]] = counts.get(story["region"], 0) + 1
    for region, _ in content.AGATE:
        counts[region] = counts.get(region, 0)
    order = ["EUROPE", "ASIA", "AMERICAS", "MIDDLE EAST", "AFRICA", "OCEANIA", "WORLD"]
    shown = [r for r in order if counts.get(r)] + [r for r in counts if r not in order and counts[r]]

    vhair(506, top + 16, top + 92, color=RULE)
    caps("REGION", 7.6, "sansb", 518, top + 18, color=MUTED, tracking=1.2, cell="map")
    caps("PINNED", 7.6, "sansb", 640, top + 18, color=MUTED, tracking=1.2, align="right", cell="map")
    hair(518, top + 28, 640, color=RULE, width=0.8)
    for i, region in enumerate(shown[:14]):
        col, row = i % 3, i // 3
        x = 518 + col * 162
        y = top + 34 + row * 17.0
        cell(f"region{i}", x, y, x + 122, y + 14)
        caps(region, 8.4, "sansb", x, y + 1.2, color=ACCENT, tracking=1.0, limit=104, cell=f"region{i}")
        text(x + 122, y, str(counts[region]), 11.0, "sansb", color=INK, align="right", cell=f"region{i}")


def agate() -> None:
    top = 882
    head = f"ALSO ON {content.DAY_WORD} \u00b7 THE REST OF THE DAY IN {len(content.AGATE)} LINES"
    caps(head, 10.0, "sansb", M, top, color=INK, tracking=2.2, limit=CW, cell="agate")
    hair(M, top + 14, W - M, color=INK, width=1.2)
    cols, gap = 3, 14
    cw = (CW - (cols - 1) * gap) / cols
    per = (len(content.AGATE) + cols - 1) // cols
    for i, (region, line) in enumerate(content.AGATE):
        col, row = divmod(i, per)
        x = M + col * (cw + gap)
        y = top + 17 + row * 11.0
        cell(f"agate{i}", x, y, x + cw, y + 10.4)
        tag_w = caps(region, 7.4, "sansb", x, y + 2.0, color=ACCENT, tracking=0.8,
                     limit=cw * 0.4, cell=f"agate{i}", name="region")
        text(x + tag_w + 6, y, line, 9.8, "sans", color=INK, limit=cw - tag_w - 8, cell=f"agate{i}")


def footer() -> None:
    hair(M, 992, W - M, color=RULE, width=0.9)
    caps("REPORTED BY AL JAZEERA, BBC NEWS, THE GUARDIAN, THE JERUSALEM POST, EURONEWS AND OTHERS",
         7.4, "sansb", M, 996, color=MUTED, tracking=0.9, limit=CW * 0.82, cell="footer")
    caps("SOURCES: SEE SOURCES.MD", 7.4, "sansb", W - M, 996, color=MUTED, tracking=0.9,
         align="right", cell="footer")


# -------------------------------------------------------------------- audit

def audit() -> dict:
    for c in _cells:
        x0, y0, x1, y1 = c["box"]
        if x0 < M - 0.6 or y0 < M - 0.6 or x1 > W - M + 0.6 or y1 > W - M + 0.6:
            _issues.append(f"{c['name']}: box {c['box']} breaks the {M}px margin")
    for p in _placed:
        if p["x"] < M - 0.6 or p["x"] + p["w"] > W - M + 0.6:
            _issues.append(f"{p['cell']}/{p['name']}: text runs outside the margin")
        if p["y"] < M - 0.6 or p["y"] + p["h"] > W - M + 0.6:
            _issues.append(f"{p['cell']}/{p['name']}: sits outside the page")
    for i, a in enumerate(_cells):
        for b in _cells[i + 1:]:
            ax0, ay0, ax1, ay1 = a["box"]
            bx0, by0, bx1, by1 = b["box"]
            ox = min(ax1, bx1) - max(ax0, bx0)
            oy = min(ay1, by1) - max(ay0, by0)
            if ox > 0.9 and oy > 0.9:
                _issues.append(f"overlap {a['name']} / {b['name']} by {ox:.1f}x{oy:.1f}")
    # a rule that runs through a line of text reads, at thumbnail size, as garbled
    for p in _placed:
        for ry, rx0, rx1 in _rules:
            if p["x"] + p["w"] < rx0 - 1 or p["x"] > rx1 + 1:
                continue
            if p["y"] + 1.0 < ry < p["y"] + p["h"] - 1.0:
                _issues.append(f"{p['cell']}/{p['name']}: a rule at y={ry:.1f} runs through this text")
                break
    boxes = {c["name"]: c["box"] for c in _cells}
    for p in _placed:
        b = boxes.get(p["cell"])
        if not b:
            continue
        if p["x"] < b[0] - 1 or p["y"] < b[1] - 2.5 or p["y"] + p["h"] > b[3] + 2.5:
            _issues.append(f"{p['cell']}/{p['name']}: text escapes its cell")
    return {"cells": len(_cells), "text_runs": len(_placed), "issues": _issues}


def main() -> None:
    header()
    figure_rail()
    lead()
    second_leads()
    brief_cards()
    map_band()
    agate()
    footer()
    report = audit()
    out = Path(os.environ.get("RENDER_OUT") or (Path(__file__).resolve().parents[1] / "entry.png"))
    image.resize((W, W), Image.LANCZOS).save(out, "PNG", optimize=True)
    print(f"wrote {out} ({out.stat().st_size} bytes)")
    print(f"cells {report['cells']}  text runs {report['text_runs']}  issues {len(report['issues'])}")
    for issue in report["issues"][:30]:
        print(" !", issue)


if __name__ == "__main__":
    main()
