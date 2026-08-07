"""
Convert a portrait photo into a clean, monochrome ASCII-art SVG that "types"
itself in like a terminal, then holds — and fades out at the edges so the face
dissolves into the card instead of ending on a hard rectangle.

Monochrome is deliberate: per-character rainbow color is what makes ASCII
portraits look noisy. One fill color + a good density ramp + high contrast
(so a busy background washes out to blank) reads as neat and legible.

GitHub renders SVGs embedded via <img> and runs their SMIL animations there
(JS does not run). Each row is revealed with a left-to-right clip wipe plus a
small block cursor riding the wipe edge, staggered top -> bottom, so the whole
portrait prints once and freezes.

    python scripts/make_ascii_svg.py [source-prepped.png] [assets/ascii-face.svg]

Env:
    STATIC=1   emit the frozen end-state (no animation) for quick previews.

Technique adapted from Avi Vashishta's animated-README writeup; palette and
framing retuned to the Dracula theme used across this profile.
"""
from PIL import Image, ImageEnhance, ImageFilter
import html
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import palette as P  # noqa: E402
# defaults to the prepped grayscale image (see prep_photo.py), which already
# has the background removed + local contrast applied.
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "source-prepped.png")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "assets", "ascii-face.svg")

COLS = 100
ROWS = 53
CELL_W = 8
CELL_H = 15
RAMP = " .`:-=+*cs#%@"  # bright(sparse) -> dark(dense); leading space clears bg

# the prepped image already has bg removed + CLAHE local contrast, so only
# light global tuning is needed here.
CONTRAST = 1.05
BRIGHTNESS = 1.0
GAMMA = 1.18          # >1 brightens mids -> face lands in sparser chars
SHARPEN = False
WHITE_FLOOR = 0.80    # luminance above this is forced to blank (space)

# Source crop as fractions (left, top, right, bottom). Tighten this so the head
# fills the frame; the default suits a square avatar-style headshot.
CROP = (0.13, 0.02, 0.87, 0.86)
TOP_BIAS = 0.30       # 0 = flush top, 0.5 = centered; keeps hair off the edge

PAD = 20
TITLEBAR_H = 30
STATUS_H = 30
ART_W = COLS * CELL_W
ART_H = ROWS * CELL_H
CANVAS_W = ART_W + PAD * 2
CANVAS_H = TITLEBAR_H + ART_H + STATUS_H + PAD

# see scripts/palette.py
BG = P.BG_DEEP
BG2 = P.BG_RAISED
FRAME = P.FRAME
TITLE_TEXT = P.DIM
INK = P.INK           # the single ascii color
CURSOR = P.SUCCESS

# ---- fade: fraction of the art height that dissolves at top / bottom ------
FADE_TOP = 0.10
FADE_BOTTOM = 0.22

# ---- reveal timing (one-shot; a cursor rasters top -> bottom) -------------
ROW_DUR = 0.11
STAGGER = 0.11        # == ROW_DUR -> a single cursor sweeping down

# ---- 1. sample the image into a COLS x ROWS grayscale grid ----------------
im = Image.open(SRC).convert("L")               # grayscale
if SHARPEN:
    im = im.filter(ImageFilter.UnsharpMask(radius=2, percent=140, threshold=2))
im = ImageEnhance.Brightness(im).enhance(BRIGHTNESS)
im = ImageEnhance.Contrast(im).enhance(CONTRAST)

# Monospace cells are ~2x taller than wide, so sampling straight to COLSxROWS
# would squash the face. Fit the photo into the cell grid's true aspect
# (COLS*CELL_W : ROWS*CELL_H) on white, preserving proportions, then sample.
# CROP trims the source first so the head fills the frame and the bottom fade
# lands on shoulders rather than a hard chest edge.
sw, sh = im.size
l, t, r, b = CROP
im = im.crop((int(sw * l), int(sh * t), int(sw * r), int(sh * b)))

cw, ch = im.size
cell_aspect = (COLS * CELL_W) / (ROWS * CELL_H)
scale = min((COLS * CELL_W) / cw, (ROWS * CELL_H) / ch)
fw, fh = max(1, int(cw * scale)), max(1, int(ch * scale))
fitted = im.resize((fw, fh), Image.LANCZOS)

frame = Image.new("L", (COLS * CELL_W, ROWS * CELL_H), 255)
frame.paste(fitted, ((COLS * CELL_W - fw) // 2, int((ROWS * CELL_H - fh) * TOP_BIAS)))

im = frame.resize((COLS, ROWS), Image.LANCZOS)
px = im.load()

STATIC = bool(os.environ.get("STATIC"))  # emit frozen state for previews

rows_txt = []
for y in range(ROWS):
    chars = []
    for x in range(COLS):
        lum = px[x, y] / 255.0
        lum = pow(lum, GAMMA)
        if lum >= WHITE_FLOOR:
            chars.append(" ")
            continue
        idx = int((1.0 - lum) * (len(RAMP) - 1) + 0.5)
        idx = max(0, min(len(RAMP) - 1, idx))
        chars.append(RAMP[idx])
    rows_txt.append("".join(chars))

art_top = TITLEBAR_H + PAD * 0.35

# ---- 2. assemble SVG ------------------------------------------------------
parts = []
parts.append(
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_W}" height="{CANVAS_H}" '
    f'viewBox="0 0 {CANVAS_W} {CANVAS_H}" font-family="ui-monospace, SFMono-Regular, '
    f'Menlo, Consolas, monospace">'
)

# The fade is a luminance mask over the art layer only: white = keep, black =
# dissolve. Top and bottom bands ramp to transparent so the portrait melts into
# the card background instead of stopping on a hard edge.
parts.append(
    '<defs>'
    f'<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
    f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/>'
    f'</linearGradient>'
    f'<linearGradient id="fadegrad" x1="0" y1="0" x2="0" y2="1">'
    f'<stop offset="0" stop-color="#000"/>'
    f'<stop offset="{FADE_TOP}" stop-color="#fff"/>'
    f'<stop offset="{1.0 - FADE_BOTTOM}" stop-color="#fff"/>'
    f'<stop offset="1" stop-color="#000"/>'
    f'</linearGradient>'
    f'<mask id="fade" maskUnits="userSpaceOnUse" '
    f'x="0" y="{art_top:.1f}" width="{CANVAS_W}" height="{ART_H}">'
    f'<rect x="0" y="{art_top:.1f}" width="{CANVAS_W}" height="{ART_H}" fill="url(#fadegrad)"/>'
    f'</mask>'
    '</defs>'
)

parts.append(f'<rect width="{CANVAS_W}" height="{CANVAS_H}" rx="12" fill="url(#bg)"/>')
parts.append(f'<rect x="0.5" y="0.5" width="{CANVAS_W-1}" height="{CANVAS_H-1}" rx="12" '
             f'fill="none" stroke="{FRAME}" stroke-width="1"/>')

parts.append(f'<line x1="0" y1="{TITLEBAR_H}" x2="{CANVAS_W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>')
for i, dotcol in enumerate([P.DOT_RED, P.DOT_AMBER, P.DOT_GREEN]):
    parts.append(f'<circle cx="{PAD + i*16}" cy="{TITLEBAR_H/2}" r="5" fill="{dotcol}"/>')
parts.append(f'<text x="{CANVAS_W/2}" y="{TITLEBAR_H/2 + 4}" fill="{TITLE_TEXT}" font-size="12" '
             f'text-anchor="middle">anuvik@github: ~$ ./portrait.sh</text>')

# everything inside this group is subject to the fade mask
parts.append('<g mask="url(#fade)">')

# one <text> per row (single color -> no per-char markup, tiny file)
font_size = CELL_H * 0.86
for ry, line in enumerate(rows_txt):
    y = art_top + ry * CELL_H + CELL_H * 0.74
    row_y = art_top + ry * CELL_H
    delay = ry * STAGGER
    safe = html.escape(line)
    text = (f'<text xml:space="preserve" x="{PAD}" y="{y:.1f}" fill="{INK}" '
            f'font-size="{font_size:.1f}" textLength="{ART_W}" lengthAdjust="spacing">{safe}</text>')

    if STATIC:
        parts.append(text)
        continue

    parts.append(
        f'<clipPath id="r{ry}"><rect x="{PAD}" y="{row_y:.1f}" height="{CELL_H}" width="0">'
        f'<animate attributeName="width" from="0" to="{ART_W}" begin="{delay:.3f}s" '
        f'dur="{ROW_DUR:.2f}s" fill="freeze"/></rect></clipPath>'
    )
    parts.append(f'<g clip-path="url(#r{ry})">{text}</g>')
    parts.append(
        f'<rect y="{row_y+1:.1f}" width="{CELL_W}" height="{CELL_H-2}" fill="{CURSOR}" opacity="0">'
        f'<animate attributeName="x" from="{PAD}" to="{PAD+ART_W}" begin="{delay:.3f}s" '
        f'dur="{ROW_DUR:.2f}s" fill="freeze"/>'
        f'<set attributeName="opacity" to="0.85" begin="{delay:.3f}s"/>'
        f'<set attributeName="opacity" to="0" begin="{delay+ROW_DUR:.3f}s"/></rect>'
    )

parts.append('</g>')

# status bar with a steady blinking cursor
status_line_y = TITLEBAR_H + ART_H + PAD * 0.35
status_y = status_line_y + 19
parts.append(f'<line x1="0" y1="{status_line_y:.1f}" x2="{CANVAS_W}" y2="{status_line_y:.1f}" stroke="{FRAME}"/>')
parts.append(f'<text x="{PAD}" y="{status_y:.1f}" fill="{TITLE_TEXT}" font-size="13">'
             f'anuvik@github:~$ whoami <tspan fill="{INK}">Anuvik Thota</tspan></text>')
parts.append(f'<rect x="{PAD+212}" y="{status_y-12:.1f}" width="8" height="14" fill="{INK}">'
             f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.51;1" '
             f'dur="1s" repeatCount="indefinite"/></rect>')

parts.append("</svg>")
svg = "".join(parts)
os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
with open(OUT, "w") as f:
    f.write(svg)
print("wrote", OUT, len(svg), "bytes;", CANVAS_W, "x", CANVAS_H)
