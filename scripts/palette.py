"""
Single source of truth for the profile's colour theme: crimson / carbon /
phosphor-green.

Every SVG in assets/ was originally authored against the Dracula palette with
hex codes inlined in ten different files. Keeping the mapping here means a
future re-theme is one edit plus `python scripts/retheme.py`, instead of a
find-and-replace across every asset that silently misses one.

Roles, not names — `ACCENT` rather than `RED` — so swapping the theme again
doesn't leave variables lying about their contents.
"""

# ---- surfaces -------------------------------------------------------------
BG_DEEP = "#08090c"      # window body, darkest
BG_PANEL = "#0d0f14"     # titlebars, status bars, node fills
BG_RAISED = "#141821"    # gradient top / raised inner cards
TRACK = "#242a36"        # empty progress-bar track, axis lines
FRAME = "#2b3240"        # 1px hairline borders, dividers

# ---- ink ------------------------------------------------------------------
FG = "#e8ecf2"           # primary text
INK = "#c3ccd8"          # ascii portrait fill
DIM = "#727f92"          # captions, secondary text — 4.6:1 on BG_DEEP (WCAG AA)

# ---- accents --------------------------------------------------------------
ACCENT = "#ff2d46"       # crimson — primary brand accent, alerts
ACCENT_SOFT = "#ff6b6b"  # lighter crimson, for text on dark
SUCCESS = "#00e676"      # phosphor green — healthy, wins, prompts
SUCCESS_DIM = "#0f9d58"  # deeper green, secondary
MINT = "#7dffb8"         # pale mint — paths, panel headings, labels
WARN = "#ffab40"         # amber — the third tier / mid states
HILITE = "#ffd54f"       # warm yellow — numeric callouts

# ---- traffic-light dots ---------------------------------------------------
DOT_RED = "#ff5f56"
DOT_AMBER = "#ffbd2e"
DOT_GREEN = "#27c93f"

# ---- gradients ------------------------------------------------------------
# Border gradient: crimson -> ember -> green. Reads as a heat sweep rather than
# the old three-way pastel, and both endpoints are theme accents.
BORDER_STOPS = (ACCENT, "#ff7043", SUCCESS)

# Old Dracula hex -> new role. Used by retheme.py to rewrite the hand-authored
# SVGs. Ordered longest-lived-first is irrelevant (all are 7 chars) but keys
# must be lowercase; retheme.py lowercases the source before matching.
DRACULA_MAP = {
    # surfaces
    "#101018": BG_DEEP,
    "#10111a": BG_PANEL,
    "#1c1d2b": BG_RAISED,
    "#191a26": BG_RAISED,
    "#44475a": TRACK,
    "#30363d": FRAME,
    # ink
    "#f8f8f2": FG,
    "#c9d1d9": INK,
    "#6272a4": DIM,
    # accents
    "#bd93f9": ACCENT,        # purple  -> crimson
    "#ff79c6": ACCENT_SOFT,   # pink    -> soft crimson
    # Cyan carried its own role (paths, panel headings, node labels). Mapping it
    # onto SUCCESS too would flatten that against the green prompts, so it gets
    # the paler mint instead — still in-family, still distinguishable.
    "#8be9fd": MINT,          # cyan    -> pale mint
    "#50fa7b": SUCCESS,       # green   -> phosphor green
    "#ff5555": ACCENT,        # red     -> crimson
    "#ffb86c": WARN,          # orange  -> amber
    "#f1fa8c": HILITE,        # yellow  -> warm yellow
    # traffic lights stay as-is; listed so retheme reports full coverage
    "#ff5f56": DOT_RED,
    "#ffbd2e": DOT_AMBER,
    "#27c93f": DOT_GREEN,
}
