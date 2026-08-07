"""
Rewrite the hand-authored SVGs in assets/ from the old Dracula palette to the
crimson/carbon/green theme defined in palette.py.

Run after editing palette.py:

    python scripts/retheme.py            # rewrite assets/*.svg in place
    python scripts/retheme.py --check    # report leftover off-palette hex, exit 1

hero.svg and ascii-face.svg are skipped — they are generated, so their colours
come from make_hero_svg.py / make_ascii_svg.py importing palette.py directly.

A blanket hex swap is not sufficient on its own: Dracula's cyan and green both
map to one phosphor green, which would erase distinctions the diagrams encode
(the four GNN node types, pod border vs. health dot). PER_FILE below re-splits
those cases after the global pass.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import palette as P  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "assets")

GENERATED = {"hero.svg", "ascii-face.svg"}

# The old gradient had three stops; the new one keeps three but re-coloured.
GRADIENT_RE = re.compile(
    r'(<linearGradient id="nbd".*?</linearGradient>)', re.S
)
NEW_GRADIENT = (
    '<linearGradient id="nbd" x1="0" y1="0" x2="1" y2="1">'
    f'<stop offset="0" stop-color="{P.BORDER_STOPS[0]}"/>'
    f'<stop offset="0.55" stop-color="{P.BORDER_STOPS[1]}"/>'
    f'<stop offset="1" stop-color="{P.BORDER_STOPS[2]}"/>'
    '</linearGradient>'
)

# Substitutions applied to a single file AFTER the global hex map, to restore
# contrast that the many-to-one colour mapping would otherwise flatten.
# Each entry: filename -> list of (search, replace) applied in order.
PER_FILE = {
    # Four node types must stay visually distinct. Post-map they'd be
    # green/crimson/green/amber; re-split the two greens.
    "card-gnn.svg": [
        # 'card' node: was purple -> crimson, but the fraud node is already
        # crimson. Give card the amber, and ip a cooler steel.
        ('stroke="#ff2d46"/>\n    <text x="205" y="80" text-anchor="middle" class="xs purple">card</text>',
         f'stroke="{P.HILITE}"/>\n    <text x="205" y="80" text-anchor="middle" class="xs yellow">card</text>'),
        # 'ip' node: amber -> steel, so it doesn't collide with card.
        ('stroke="#ffab40"/>\n    <text x="205" y="154" text-anchor="middle" class="xs orange">ip</text>',
         f'stroke="{P.DIM}"/>\n    <text x="205" y="154" text-anchor="middle" class="xs dim">ip</text>'),
        # message-passing packet rides the edges: make it warm so it reads
        # against green nodes.
        (f'<circle r="2.5" fill="{P.MINT}" class="msg">',
         f'<circle r="2.5" fill="{P.HILITE}" class="msg">'),
    ],
    # Pod borders (was cyan) and the health dots (was green) both became
    # phosphor green. Push the borders to a dimmer green so the live dot pops.
    "cloud-infra.svg": [
        (f'width="60" height="44" rx="6" fill="{P.BG_RAISED}" stroke="{P.MINT}"/>',
         f'width="60" height="44" rx="6" fill="{P.BG_RAISED}" stroke="{P.SUCCESS_DIM}"/>'),
        # prometheus panel border: dim green rather than competing with sparkline
        (f'<rect x="270" y="46" width="118" height="128" rx="10" fill="{P.BG_PANEL}" stroke="{P.MINT}"/>',
         f'<rect x="270" y="46" width="118" height="128" rx="10" fill="{P.BG_PANEL}" stroke="{P.SUCCESS_DIM}"/>'),
    ],
    # prompt box (cyan) and MCP box (green) collapsed together; split them.
    "ai-pipeline.svg": [
        (f'<rect x="18" y="58" width="78" height="28" rx="6" fill="{P.BG_PANEL}" stroke="{P.MINT}"/>',
         f'<rect x="18" y="58" width="78" height="28" rx="6" fill="{P.BG_PANEL}" stroke="{P.SUCCESS_DIM}"/>'),
        # first packet was cyan, second purple->crimson; keep them distinct
        (f'<circle r="2.5" fill="{P.MINT}" filter="url(#glow)">',
         f'<circle r="2.5" fill="{P.HILITE}" filter="url(#glow)">'),
    ],
}

# Class names in the stylesheets still say .purple/.cyan/.pink. Renaming them
# across every file is churn for no rendered difference — the fill values are
# what matter and those are rewritten. Left alone deliberately.


def retheme(text: str) -> str:
    out = GRADIENT_RE.sub(lambda _: NEW_GRADIENT, text)
    for old, new in P.DRACULA_MAP.items():
        out = re.sub(re.escape(old), new, out, flags=re.I)
    return out


def main() -> int:
    check = "--check" in sys.argv
    stale = re.compile("|".join(re.escape(k) for k in P.DRACULA_MAP
                               if k not in {P.DOT_RED, P.DOT_AMBER, P.DOT_GREEN}), re.I)

    failures = []
    for name in sorted(os.listdir(ASSETS)):
        if not name.endswith(".svg"):
            continue
        # Generated assets are never rewritten here, but --check still audits
        # them: they are committed, so a stale palette in one is a real defect.
        if name in GENERATED and not check:
            continue
        path = os.path.join(ASSETS, name)
        with open(path) as f:
            src = f.read()

        # --check verifies the committed assets are on-palette. It must NOT
        # re-run the per-file rules: those match pre-substitution text, so on an
        # already-rethemed file they "fail" by design. Only the hex sweep is a
        # meaningful assertion against committed output.
        if check:
            leftover = sorted(set(stale.findall(src)))
            if leftover:
                failures.append(f"{name}: off-palette hex remains: {leftover}")
            continue

        out = retheme(src)
        for old, new in PER_FILE.get(name, []):
            if old not in out:
                failures.append(f"{name}: per-file rule did not match: {old[:60]!r}")
            out = out.replace(old, new)

        leftover = sorted(set(stale.findall(out)))
        if leftover:
            failures.append(f"{name}: off-palette hex remains: {leftover}")
        if out != src:
            with open(path, "w") as f:
                f.write(out)
            print("rethemed", name)

    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    print("all assets on-palette" if check else "done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
