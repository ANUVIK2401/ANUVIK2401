"""
Build the unified hero banner: terminal readout on the left, animated ASCII
portrait on the right, inside one window frame.

GitHub strips <style>/CSS from markdown but DOES run SMIL inside an <img>-embedded
SVG, and it renders CSS that lives inside the SVG itself. Emitting both halves as
a single SVG (rather than two images in a table) keeps the columns locked
together at every viewport width and lets both share one frame, one gradient
border and one scanline.

    python scripts/make_hero_svg.py [source-prepped.png] [assets/hero.svg]

Env:
    STATIC=1   emit the frozen end-state (no animation) for quick previews.
"""
from PIL import Image, ImageEnhance
import html
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "source-prepped.png")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "assets", "hero.svg")

STATIC = bool(os.environ.get("STATIC"))  # emit frozen end-state for previews

# ---- portrait sampling ----------------------------------------------------
# CELL_W:CELL_H must stay near a real monospace glyph ratio (~0.6). textLength
# forces each row to exactly COLS*CELL_W, so a too-narrow cell squashes the face
# horizontally no matter how the source was sampled.
COLS = 58
ROWS = 42
CELL_W = 7
CELL_H = 11
RAMP = " .`:-=+*cs#%@"

CONTRAST = 1.05
GAMMA = 1.18
WHITE_FLOOR = 0.80
CROP = (0.13, 0.02, 0.87, 0.86)
TOP_BIAS = 0.30

FADE_TOP = 0.08
FADE_BOTTOM = 0.20

# ---- layout ---------------------------------------------------------------
TITLEBAR_H = 36
PANE_PAD = 28
ART_W = COLS * CELL_W          # 372
ART_H = ROWS * CELL_H          # 400
LEFT_W = 700
DIVIDER_X = LEFT_W
RIGHT_W = ART_W + PANE_PAD * 2
CANVAS_W = LEFT_W + RIGHT_W
# art_top (TITLEBAR_H+26) + ART_H + room for the footer caption below the fade
CANVAS_H = TITLEBAR_H + 26 + ART_H + 34

# ---- palette (Dracula, matched to terminal.svg) ---------------------------
INK = "#c9d1d9"
CURSOR = "#8be9fd"
FRAME = "#30363d"
DIM = "#6272a4"

ROW_DUR = 0.09
STAGGER = 0.09
ART_BEGIN = 0.6                # let the left pane start printing first

# ---- 1. sample the image --------------------------------------------------
im = Image.open(SRC).convert("L")
im = ImageEnhance.Contrast(im).enhance(CONTRAST)

sw, sh = im.size
l, t, r, b = CROP
im = im.crop((int(sw * l), int(sh * t), int(sw * r), int(sh * b)))

cw, ch = im.size
scale = min(ART_W / cw, ART_H / ch)
fw, fh = max(1, int(cw * scale)), max(1, int(ch * scale))
fitted = im.resize((fw, fh), Image.LANCZOS)

frame_img = Image.new("L", (ART_W, ART_H), 255)
frame_img.paste(fitted, ((ART_W - fw) // 2, int((ART_H - fh) * TOP_BIAS)))
im = frame_img.resize((COLS, ROWS), Image.LANCZOS)
px = im.load()

rows_txt = []
for y in range(ROWS):
    chars = []
    for x in range(COLS):
        lum = pow(px[x, y] / 255.0, GAMMA)
        if lum >= WHITE_FLOOR:
            chars.append(" ")
            continue
        idx = int((1.0 - lum) * (len(RAMP) - 1) + 0.5)
        chars.append(RAMP[max(0, min(len(RAMP) - 1, idx))])
    rows_txt.append("".join(chars))

# ---- 2. assemble ----------------------------------------------------------
art_x = DIVIDER_X + PANE_PAD
art_top = TITLEBAR_H + 26

p = []
p.append(
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_W}" height="{CANVAS_H}" '
    f'viewBox="0 0 {CANVAS_W} {CANVAS_H}" fill="none">'
)
p.append(
    '<defs>'
    '<linearGradient id="nbd" x1="0" y1="0" x2="1" y2="1">'
    '<stop offset="0" stop-color="#bd93f9"/><stop offset="0.5" stop-color="#8be9fd"/>'
    '<stop offset="1" stop-color="#ff79c6"/></linearGradient>'
    '<linearGradient id="pbg" x1="0" y1="0" x2="0" y2="1">'
    '<stop offset="0" stop-color="#1c1d2b"/><stop offset="1" stop-color="#101018"/>'
    '</linearGradient>'
    '<filter id="glow" x="-60%" y="-60%" width="220%" height="220%">'
    '<feGaussianBlur stdDeviation="2.5" result="b"/>'
    '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
    f'<linearGradient id="fadegrad" x1="0" y1="0" x2="0" y2="1">'
    f'<stop offset="0" stop-color="#000"/>'
    f'<stop offset="{FADE_TOP}" stop-color="#fff"/>'
    f'<stop offset="{1.0 - FADE_BOTTOM}" stop-color="#fff"/>'
    f'<stop offset="1" stop-color="#000"/></linearGradient>'
    f'<mask id="fade" maskUnits="userSpaceOnUse" x="{DIVIDER_X}" y="{art_top}" '
    f'width="{RIGHT_W}" height="{ART_H}">'
    f'<rect x="{DIVIDER_X}" y="{art_top}" width="{RIGHT_W}" height="{ART_H}" fill="url(#fadegrad)"/>'
    f'</mask>'
    '</defs>'
)

# STATIC previews must also defeat the CSS reveal: .line starts at opacity 0 and
# .bar at scaleX(0), so a renderer that ignores CSS animation shows an empty pane.
static_css = """
    .line { opacity: 1 !important; animation: none !important; }
    .bar { transform: scaleX(1) !important; animation: none !important; }
    .cursor, .scan { animation: none !important; }
""" if STATIC else ""

p.append("""<style>
    .mono { font-family: 'SF Mono','Fira Code','JetBrains Mono',Menlo,Consolas,monospace; font-size: 14px; }
    .big { font-size: 21px; font-weight: bold; }
    .sm { font-size: 12px; } .xs { font-size: 11px; }
    .green { fill: #50fa7b; } .cyan { fill: #8be9fd; } .purple { fill: #bd93f9; }
    .pink { fill: #ff79c6; } .yellow { fill: #f1fa8c; } .orange { fill: #ffb86c; }
    .fg { fill: #f8f8f2; } .dim { fill: #6272a4; }
    .line { opacity: 0; animation: pop .35s ease-out forwards; }
    @keyframes pop { from { opacity: 0; transform: translateX(-6px); } to { opacity: 1; transform: translateX(0); } }
    .l1{animation-delay:.2s} .l2{animation-delay:.7s} .l3{animation-delay:1.3s}
    .l4{animation-delay:1.7s} .l5{animation-delay:2.1s} .l6{animation-delay:2.5s}
    .l7{animation-delay:3.1s} .l8{animation-delay:3.5s} .l9{animation-delay:3.9s}
    .l10{animation-delay:4.5s} .l11{animation-delay:4.9s} .l12{animation-delay:5.3s}
    .cursor { animation: blink 1s step-end infinite; }
    @keyframes blink { 50% { opacity: 0; } }
    .bar { animation: grow 1.2s ease-out forwards; transform-origin: left; transform: scaleX(0); }
    @keyframes grow { to { transform: scaleX(1); } }
    .b1{animation-delay:2.2s} .b2{animation-delay:2.6s} .b3{animation-delay:3.0s}
    .scan { animation: scan 4s linear infinite; }
    @keyframes scan { 0%{opacity:.05} 50%{opacity:.12} 100%{opacity:.05} }
""" + static_css + """  </style>""")

# window chrome
p.append(f'<rect x="1" y="1" width="{CANVAS_W-2}" height="{CANVAS_H-2}" rx="12" '
         f'fill="url(#pbg)" stroke="url(#nbd)" stroke-width="2"/>')
p.append(f'<rect x="1" y="1" width="{CANVAS_W-2}" height="{CANVAS_H-2}" rx="12" '
         f'fill="#bd93f9" class="scan" opacity=".05"/>')
p.append(f'<path d="M1 13 A12 12 0 0 1 13 1 H{CANVAS_W-13} A12 12 0 0 1 {CANVAS_W-1} 13 '
         f'V{TITLEBAR_H} H1 Z" fill="#10111a"/>')
for i, c in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
    p.append(f'<circle cx="{24 + i*20}" cy="19" r="6" fill="{c}"/>')
p.append(f'<text x="{CANVAS_W/2}" y="24" text-anchor="middle" class="mono sm dim">'
         f'anuvik@ai-systems — zsh — {CANVAS_W}x{CANVAS_H}</text>')

# vertical divider between panes
p.append(f'<line x1="{DIVIDER_X}" y1="{TITLEBAR_H}" x2="{DIVIDER_X}" y2="{CANVAS_H-1}" '
         f'stroke="{FRAME}" stroke-width="1"/>')

# ---- left pane: terminal readout -----------------------------------------
# Left-pane content is authored against fixed y coords ending at LEFT_CONTENT_H;
# nudge the whole group so it stays optically centred against the taller right
# pane whenever CANVAS_H changes.
LEFT_CONTENT_H = 424
left_dy = max(0, (CANVAS_H - TITLEBAR_H - LEFT_CONTENT_H) / 2)
p.append(f'<g class="mono" transform="translate(0,{left_dy:.1f})">')
p.append('<text x="28" y="74" class="line l1"><tspan class="green">➜</tspan>'
         '<tspan class="cyan" dx="10">~</tspan><tspan class="fg" dx="10">./anuvik --init</tspan></text>')
p.append('<text x="28" y="104" class="line l2 big" filter="url(#glow)">'
         '<tspan class="purple" style="fill:url(#nbd)" letter-spacing="1">ANUVIK THOTA</tspan>'
         '<tspan class="dim" dx="12">·</tspan>'
         '<tspan class="cyan" dx="12">AI / ML Systems Engineer</tspan></text>')
p.append('<text x="28" y="128" class="line l3"><tspan class="dim">└─</tspan>'
         '<tspan class="fg" dx="8">MSCS @ USC</tspan><tspan class="dim" dx="8">·</tspan>'
         '<tspan class="fg" dx="8">ex-Oracle SWE II</tspan><tspan class="dim" dx="8">·</tspan>'
         '<tspan class="fg" dx="8">AI FDE @ MSRcosmos</tspan></text>')

p.append('<text x="28" y="168" class="line l4"><tspan class="green">➜</tspan>'
         '<tspan class="cyan" dx="10">~</tspan><tspan class="fg" dx="10">htop --skills</tspan></text>')

# Everything in the left pane must stay inside DIVIDER_X - LEFT_GUTTER, or it
# bleeds across the divider into the portrait. Derive the track from the divider
# rather than hardcoding, so changing LEFT_W can never re-introduce the overlap.
LEFT_GUTTER = 28
PCT_W = 42                                   # room for the "94%" label
BAR_X = 220
BAR_MAX_X = DIVIDER_X - LEFT_GUTTER - PCT_W  # bar track ends here
BAR_W = BAR_MAX_X - BAR_X
PCT_X = DIVIDER_X - LEFT_GUTTER              # right-anchored label

bars = [
    ("LLM Inference", "pink", "#ff79c6", 0.94, "94%", "l5", "b1", 194),
    ("Agents / LangGraph", "cyan", "#8be9fd", 0.90, "90%", "l6", "b2", 222),
    ("Prod Observability", "green", "#50fa7b", 0.96, "96%", "l7", "b3", 250),
]
for label, cls, col, frac, pct, lc, bc, y in bars:
    p.append(f'<text x="28" y="{y}" class="line {lc}"><tspan class="{cls}">{label}</tspan></text>')
    p.append(f'<rect x="{BAR_X}" y="{y-10}" width="{BAR_W}" height="12" rx="6" '
             f'fill="#44475a" class="line {lc}"/>')
    p.append(f'<rect x="{BAR_X}" y="{y-10}" width="{BAR_W*frac:.0f}" height="12" rx="6" '
             f'fill="{col}" class="bar {bc}" filter="url(#glow)"/>')
    p.append(f'<text x="{PCT_X}" y="{y}" class="line {lc} {cls} sm" text-anchor="end">{pct}</text>')

p.append('<text x="28" y="292" class="line l8"><tspan class="green">➜</tspan>'
         '<tspan class="cyan" dx="10">~</tspan>'
         '<tspan class="fg" dx="10">grep -r "impact" career/</tspan></text>')
p.append('<text x="28" y="318" class="line l9"><tspan class="yellow">37K+</tspan>'
         '<tspan class="fg" dx="8">tenants</tspan><tspan class="dim" dx="10">|</tspan>'
         '<tspan class="yellow" dx="10">72%</tspan><tspan class="fg" dx="8">MTTR cut</tspan>'
         '<tspan class="dim" dx="10">|</tspan><tspan class="yellow" dx="10">92%</tspan>'
         '<tspan class="fg" dx="8">ROC-AUC GNN</tspan><tspan class="dim" dx="10">|</tspan>'
         '<tspan class="orange" dx="10">INT4</tspan><tspan class="fg" dx="8">Pareto</tspan></text>')

p.append('<text x="28" y="360" class="line l10"><tspan class="green">➜</tspan>'
         '<tspan class="cyan" dx="10">~</tspan><tspan class="fg" dx="10">./contact --hire</tspan></text>')
p.append('<text x="28" y="386" class="line l11"><tspan class="pink">✉</tspan>'
         '<tspan class="cyan" dx="10">anuvikt@gmail.com</tspan><tspan class="dim" dx="14">·</tspan>'
         '<tspan class="purple" dx="14">⌖</tspan><tspan class="fg" dx="10">Los Angeles, CA</tspan></text>')
p.append('<text x="28" y="424" class="line l12"><tspan class="green">➜</tspan>'
         '<tspan class="cyan" dx="10">~</tspan><tspan class="fg cursor" dx="10">▊</tspan></text>')
p.append('</g>')

# ---- right pane: ascii portrait ------------------------------------------
p.append(f'<text x="{art_x}" y="{TITLEBAR_H + 14}" class="mono xs dim">'
         f'<tspan class="green">➜</tspan> ./portrait.sh <tspan class="dim">--ascii</tspan></text>')

p.append('<g mask="url(#fade)">')
font_size = CELL_H * 0.86
for ry, line in enumerate(rows_txt):
    y = art_top + ry * CELL_H + CELL_H * 0.74
    row_y = art_top + ry * CELL_H
    delay = ART_BEGIN + ry * STAGGER
    safe = html.escape(line)
    text = (f'<text xml:space="preserve" x="{art_x}" y="{y:.1f}" fill="{INK}" '
            f'class="mono" font-size="{font_size:.1f}" textLength="{ART_W}" '
            f'lengthAdjust="spacing">{safe}</text>')

    if STATIC:
        p.append(text)
        continue

    p.append(
        f'<clipPath id="r{ry}"><rect x="{art_x}" y="{row_y:.1f}" height="{CELL_H}" width="0">'
        f'<animate attributeName="width" from="0" to="{ART_W}" begin="{delay:.3f}s" '
        f'dur="{ROW_DUR:.2f}s" fill="freeze"/></rect></clipPath>'
    )
    p.append(f'<g clip-path="url(#r{ry})">{text}</g>')
    p.append(
        f'<rect y="{row_y+1:.1f}" width="{CELL_W}" height="{CELL_H-2}" fill="{CURSOR}" opacity="0">'
        f'<animate attributeName="x" from="{art_x}" to="{art_x+ART_W}" begin="{delay:.3f}s" '
        f'dur="{ROW_DUR:.2f}s" fill="freeze"/>'
        f'<set attributeName="opacity" to="0.85" begin="{delay:.3f}s"/>'
        f'<set attributeName="opacity" to="0" begin="{delay+ROW_DUR:.3f}s"/></rect>'
    )
p.append('</g>')

# right pane footer caption
p.append(f'<text x="{art_x}" y="{CANVAS_H - 18}" class="mono xs dim">'
         f'<tspan class="dim">whoami</tspan> <tspan class="fg">anuvik</tspan>'
         f'<tspan class="dim" dx="8">·</tspan><tspan class="purple" dx="8">{COLS}x{ROWS}</tspan>'
         f'<tspan class="dim" dx="8">·</tspan><tspan class="green" dx="8">rendered</tspan></text>')

p.append("</svg>")
svg = "".join(p)
os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
with open(OUT, "w") as f:
    f.write(svg)
print("wrote", OUT, len(svg), "bytes;", CANVAS_W, "x", CANVAS_H)
