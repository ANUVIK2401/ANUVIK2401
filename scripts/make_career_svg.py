"""
Build the career timeline as an SVG panel.

Replaces a ```diff fenced block. That block relied on '+' / '!' line prefixes
for colour, but GitHub renders '!' lines as dark olive on a green wash — nearly
unreadable, and it ignores the profile's palette entirely. Rendering the same
content as an SVG puts contrast under our control and matches the other panels.

    python scripts/make_career_svg.py [assets/career.svg]
"""
import html
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import palette as P  # noqa: E402

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "assets", "career.svg")

# (role line, location, [bullets]) — role/company/date carried in one header.
ROLES = [
    (
        "May 2026 — now", "MSRcosmos LLC", "AI Forward Deployed SWE Intern", "Los Angeles, CA",
        [
            "LangGraph multi-agent service on AWS — Sage X3 → Sage Intacct ERP migration",
            "Pilot cut manual reconciliation ~70% across 10,000+ GL/AP/AR records",
            "Sage X3 extraction on Databricks + PySpark · 15+ financial tables into Delta",
            "Sage REST APIs + MCP agent tooling · ~85% auto-approved above threshold",
            "Per-entity turnaround 3 days → under 6 hours across 12 client entities",
        ],
    ),
    (
        "Jun — Sep 2025", "USC", "AI/ML Research Intern", "Los Angeles, CA",
        [
            "DQN reward + state-action redesign → RL training 3x faster: ~6h → under 2h",
            "Fixed multi-GPU data-loader bottlenecks → +18% agent task completion",
            "FastAPI + PostgreSQL experiment tracking · 5+ parallel GPU runs · 4+ hrs/wk saved",
        ],
    ),
    (
        "Jul 2022 — Jan 2025", "Oracle", "Software Engineer II", "Hyderabad, IN",
        [
            "Prometheus/Grafana observability for Oracle NSX · 37,000+ enterprise tenants",
            "40+ dashboards and alert rules · SLOs on CPU, memory, p99 latency",
            "Real-time API diagnostics over 1M+ endpoints → P1 MTTR 90 → 25 min",
            "NetSuite SQL query-plan + index restructuring → 30% P50 latency cut",
            "CLI toolchain + Jenkins CI/CD adopted by 4 teams · release cycles −35%",
            "Docker/K8s on OCI with custom-metric HPA · held p99 SLOs at 2x peak load",
        ],
    ),
]

EDU = [
    ("Jan 2025 — Dec 2026", "USC", "MS Computer Science", "GPA 3.85"),
    ("Jun 2022", "Vasavi College of Engineering, Osmania University", "BTech CS", "GPA 3.58"),
]

# ---- layout ---------------------------------------------------------------
W = 820
PAD = 24
TITLEBAR_H = 34
RAIL_X = PAD + 6          # vertical timeline rail
TEXT_X = RAIL_X + 22      # all text hangs right of the rail
ROLE_GAP = 15             # header -> first bullet
BULLET_H = 20
BLOCK_GAP = 24            # between roles
EDU_GAP = 20

# Derive height from content so adding a bullet never overflows the frame.
y = TITLEBAR_H + 26
for *_head, bullets in ROLES:
    y += ROLE_GAP + len(bullets) * BULLET_H + BLOCK_GAP
y += 8 + EDU_GAP + len(EDU) * BULLET_H
H = y + PAD

p = []
p.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
         f'viewBox="0 0 {W} {H}" fill="none">')
p.append(
    '<defs>'
    '<linearGradient id="nbd" x1="0" y1="0" x2="1" y2="1">'
    f'<stop offset="0" stop-color="{P.BORDER_STOPS[0]}"/>'
    f'<stop offset="0.55" stop-color="{P.BORDER_STOPS[1]}"/>'
    f'<stop offset="1" stop-color="{P.BORDER_STOPS[2]}"/></linearGradient>'
    '<linearGradient id="pbg" x1="0" y1="0" x2="0" y2="1">'
    f'<stop offset="0" stop-color="{P.BG_RAISED}"/><stop offset="1" stop-color="{P.BG_DEEP}"/>'
    '</linearGradient>'
    '<linearGradient id="rail" x1="0" y1="0" x2="0" y2="1">'
    f'<stop offset="0" stop-color="{P.ACCENT}"/>'
    f'<stop offset="1" stop-color="{P.SUCCESS}"/></linearGradient>'
    '<filter id="glow" x="-60%" y="-60%" width="220%" height="220%">'
    '<feGaussianBlur stdDeviation="2" result="b"/>'
    '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
    '</defs>'
)
p.append(f"""<style>
  .mono {{ font-family:'SF Mono','Fira Code','JetBrains Mono',Menlo,Consolas,monospace; font-size:13px; }}
  .sm {{ font-size:11.5px; }} .xs {{ font-size:11px; }}
  .co {{ fill:{P.FG}; font-weight:bold; }}
  .role {{ fill:{P.MINT}; }}
  .date {{ fill:{P.HILITE}; }}
  .loc {{ fill:{P.DIM}; }}
  .b {{ fill:{P.INK}; }}
  .dot {{ fill:{P.DIM}; }}
  .edu {{ fill:{P.SUCCESS}; }}
</style>""")

# frame + titlebar
p.append(f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="12" '
         f'fill="url(#pbg)" stroke="url(#nbd)" stroke-width="2"/>')
p.append(f'<path d="M1 13 A12 12 0 0 1 13 1 H{W-13} A12 12 0 0 1 {W-1} 13 '
         f'V{TITLEBAR_H} H1 Z" fill="{P.BG_PANEL}"/>')
for i, c in enumerate([P.DOT_RED, P.DOT_AMBER, P.DOT_GREEN]):
    p.append(f'<circle cx="{20 + i*17}" cy="17" r="5" fill="{c}"/>')
p.append(f'<text x="{W/2}" y="21" text-anchor="middle" class="mono xs loc">'
         f'career — git log --stat --reverse</text>')

# timeline rail spans the role blocks only (not education)
cur = TITLEBAR_H + 26
rail_top = cur - 6
blocks = []
for date, company, role, loc, bullets in ROLES:
    blocks.append(cur)
    p.append(f'<text x="{TEXT_X}" y="{cur}" class="mono">'
             f'<tspan class="co">{html.escape(company)}</tspan>'
             f'<tspan class="loc" dx="9">·</tspan>'
             f'<tspan class="role" dx="9">{html.escape(role)}</tspan></text>')
    p.append(f'<text x="{W-PAD}" y="{cur}" text-anchor="end" class="mono sm">'
             f'<tspan class="date">{html.escape(date)}</tspan>'
             f'<tspan class="loc" dx="9">{html.escape(loc)}</tspan></text>')
    cur += ROLE_GAP
    for b in bullets:
        cur += BULLET_H - 6
        p.append(f'<text x="{TEXT_X}" y="{cur}" class="mono sm">'
                 f'<tspan class="dot">▸</tspan>'
                 f'<tspan class="b" dx="8">{html.escape(b)}</tspan></text>')
        cur += 6
    cur += BLOCK_GAP
rail_bot = cur - BLOCK_GAP - 6

p.append(f'<line x1="{RAIL_X}" y1="{rail_top}" x2="{RAIL_X}" y2="{rail_bot}" '
         f'stroke="url(#rail)" stroke-width="2"/>')
for by in blocks:
    p.append(f'<circle cx="{RAIL_X}" cy="{by-4}" r="4.5" fill="{P.BG_DEEP}" '
             f'stroke="{P.ACCENT}" stroke-width="2" filter="url(#glow)"/>')

# education
cur += 2
p.append(f'<line x1="{PAD}" y1="{cur-14}" x2="{W-PAD}" y2="{cur-14}" stroke="{P.FRAME}"/>')
for date, school, deg, gpa in EDU:
    cur += BULLET_H - 6
    p.append(f'<text x="{TEXT_X}" y="{cur}" class="mono sm">'
             f'<tspan class="edu">◆</tspan>'
             f'<tspan class="co" dx="8">{html.escape(school)}</tspan>'
             f'<tspan class="loc" dx="8">·</tspan>'
             f'<tspan class="b" dx="8">{html.escape(deg)}</tspan></text>')
    p.append(f'<text x="{W-PAD}" y="{cur}" text-anchor="end" class="mono sm">'
             f'<tspan class="date">{html.escape(date)}</tspan>'
             f'<tspan class="loc" dx="9">{html.escape(gpa)}</tspan></text>')
    cur += 6

p.append("</svg>")
svg = "".join(p)
os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
with open(OUT, "w") as f:
    f.write(svg)
print("wrote", OUT, len(svg), "bytes;", W, "x", H)
