"""Generates the environment diagram (SVG) for the Controller verification plan."""

def box(x, y, w, h, title, lines, fill, stroke, tcol):
    s = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{fill}" stroke="{stroke}" stroke-width="1.2"/>'
    s += f'<text x="{x+w/2}" y="{y+17}" text-anchor="middle" font-weight="bold" font-size="10.5" fill="{tcol}">{title}</text>'
    for i, l in enumerate(lines):
        s += f'<text x="{x+w/2}" y="{y+33+i*12}" text-anchor="middle" font-size="8.2" fill="{tcol}">{l}</text>'
    return s

def group(x, y, w, h, title, col, dash="5,4"):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="none" stroke="{col}" '
            f'stroke-width="1" stroke-dasharray="{dash}" opacity=".8"/>'
            f'<text x="{x+w/2}" y="{y+15}" text-anchor="middle" font-weight="bold" font-size="10.5" fill="{col}">{title}</text>')

def arrow(x1, y1, x2, y2, col, dash=None, mid=None):
    d = f' stroke-dasharray="{dash}"' if dash else ''
    return (f'<path d="M{x1},{y1} L{x2},{y2}" stroke="{col}" stroke-width="1.5" fill="none"{d} marker-end="url(#a{col[1:]})"/>')

def poly(pts, col, dash=None, head=True):
    d = f' stroke-dasharray="{dash}"' if dash else ''
    p = " ".join(f"{x},{y}" for x, y in pts)
    m = f' marker-end="url(#a{col[1:]})"' if head else ''
    return f'<polyline points="{p}" stroke="{col}" stroke-width="1.5" fill="none"{d}{m}/>'

PURPLE=("#eeeefb","#6b5bd2","#3a2f9c"); TEAL=("#e1f3ec","#2e9e7c","#0f6b50")
BROWN=("#fbecd6","#b5772a","#7a4a0e"); DUT=("#f1efe9","#555555","#333333")
RED=("#fbe9e4","#c4573a","#8a2f15"); BLUE=("#e6effa","#2f6fb5","#1b4a85")
GREEN=("#eaf5df","#5a9a2a","#37661a"); PINK=("#fbe6ee","#b83a6a","#8a1c48")
colors=["#2e9e7c","#c4573a","#5a9a2a","#2f6fb5","#b83a6a","#6b5bd2","#888888","#d08a00"]

o = []
o.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 920 680" font-family="Arial, Helvetica, sans-serif">')
o.append('<defs>' + "".join(
    f'<marker id="a{c[1:]}" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="{c}"/></marker>'
    for c in colors) + '</defs>')

# groups
o.append(group(8, 8, 192, 330, "Stimulus", "#8b7fe0"))
o.append(group(214, 8, 192, 330, "APB agent (master, clk input)", "#2e9e7c"))
o.append(group(618, 8, 150, 330, "Output / slave agents", "#e0805f"))

# stimulus
o.append(box(22, 34, 164, 52, "Virtual sequence", ["program kind · test type · num kernels", "builds + loads + runs"], *PURPLE))
o.append(box(22, 98, 164, 66, "Program builder", ["CFG · SCC · loop guards", "register manager · fill words", "validate · encode"], *PURPLE))
o.append(box(22, 176, 164, 54, "ctrl_program item", ["VLIW words[ ] · CR init[ ]", "metadata (loops, BR targets)"], *BROWN))
o.append(box(22, 242, 164, 80, "Generation parameters", ["block / loop / branch weights", "LR-op mix · hazard knobs", "APB gap prob. · fill policy", "error-injection probs"], *BROWN))

# APB agent
o.append(box(228, 34, 164, 50, "Sequencer", ["pulls apb items from", "the active sequence"], *TEAL))
o.append(box(228, 98, 164, 94, "Driver", ["word -> APB writes (inactive", "IMEM / CR bank, swap reg)", "random idle gaps between", "transfers, @(posedge clk)", "reads status / error regs"], *TEAL))
o.append(box(228, 206, 164, 116, "Monitor", ["psel / penable / pwrite /", "paddr / pwdata", "pready / prdata / pslverr", "-> apb_item, broadcast to", "reference model + scoreboard"], *TEAL))

# DUT
o.append(f'<rect x="424" y="8" width="176" height="330" rx="8" fill="{DUT[0]}" stroke="{DUT[1]}" stroke-width="1.2"/>')
o.append(f'<text x="512" y="26" text-anchor="middle" font-weight="bold" font-size="11" fill="{DUT[2]}">DUT - CTRL stage</text>')
for i, t in enumerate(["APB slave", "inst mem (2 banks x 128)", "PC + dual-read fetch", "COND evaluator", "LR ALU x3 lanes", "LR file 16 x 32b", "CR file 2 x 16 x 32b", "bus packer (4 VLIW buses)", "XMEM read-address gen"]):
    o.append(f'<text x="512" y="{58+i*28}" text-anchor="middle" font-size="9" fill="{DUT[2]}">{t}</text>')
o.append(f'<text x="512" y="326" text-anchor="middle" font-size="8" fill="#888">internal state: not on boundary</text>')

# outputs
o.append(box(632, 34, 122, 110, "VLIW bus agent", ["monitor-only", "mult / acc / aaq / str", "_vliw_bus every cycle", "-> bus_item", "(cycle, 4 buses)"], *RED))
o.append(box(632, 158, 122, 168, "Cache Unit agent", ["CRM + DMA model", "bank tags: tag/table/flush", "tag miss -> stall CTRL", "(signal TBD)", "\"mini mind\" = DMA fill", "policy: JIT, slow, bursty,", "targeted (RM look-ahead)", "tables: jump_back, reps"], *RED))

# scoreboards
o.append(group(782, 8, 130, 330, "Scoreboards", "#7aa84a", "none"))
o.append(box(790, 34, 114, 56, "Bus scoreboard", ["4 buses / cycle", "predicted vs observed"], *GREEN))
o.append(box(790, 102, 114, 56, "XMEM scoreboard", ["xmem_read_addr / en", "predicted vs observed"], *GREEN))
o.append(box(790, 170, 114, 56, "APB scoreboard", ["prdata / pready", "pslverr predicted"], *GREEN))
o.append(box(790, 244, 114, 82, "Coverage subscriber", ["per-word metadata", "from reference model", "ops . hazards . branches", "stall x event cross"], *PINK))

# reference model
o.append(box(424, 450, 336, 100, "Reference model (cycle-accurate CTRL ISS)", ["state: PC . active IMEM/CR bank . LR[16] . CR[2][16] . halted", "per cycle: fetch . read snapshot . COND . 3 LR lanes . pack buses", "snapshot for own reads, post-write values for buses + xmem addr", "APB map: banks, swap, pslverr on CR0/CR1 / unmapped"], *BLUE))
o.append(box(22, 450, 190, 100, "Watchdog + SVA", ["computed cycle bound", "no-bubble-on-branch", "HALT -> fetch stops", "xmem_read_en only on load"], *BROWN))
o.append(box(228, 450, 176, 100, "TB top", ["clk / rst generator", "single clock owner", "vif -> APB agent,", "bus agent, XMEM agent"], *DUT))

o.append(box(424, 354, 176, 70, "Probe agent (monitor-only)", ["bind / hier. probes inside DUT", "PC . word . branch . LR writes", "LR/CR files . bank ids -> probe_item"], *RED))
o.append(box(632, 354, 122, 70, "Probe scoreboard", ["internal state / cycle", "predicted vs observed"], *GREEN))
# arrows
g="#2e9e7c"
o.append(arrow(186, 60, 228, 60, "#2e9e7c"))                 # vseq -> sequencer
o.append(arrow(392, 140, 424, 140, "#2e9e7c"))               # driver -> DUT
o.append(arrow(600, 90, 632, 90, "#c4573a"))                 # DUT -> bus agent
o.append(arrow(600, 240, 632, 240, "#c4573a"))               # DUT -> xmem agent
o.append(poly([(632,300),(612,300),(612,270),(600,270)], "#d08a00", "4,3"))   # stall -> DUT
o.append(arrow(512, 338, 512, 354, "#c4573a", "3,3"))
o.append(arrow(600, 389, 632, 389, "#5a9a2a"))
o.append(arrow(700, 450, 700, 424, "#2f6fb5"))
o.append(arrow(754, 62, 790, 62, "#5a9a2a"))
o.append(arrow(754, 130, 790, 130, "#5a9a2a"))
o.append(poly([(392,300),(410,300),(410,346),(782,346),(782,212),(790,212)], "#5a9a2a"))  # apb monitor -> apb sb
# byte/apb stream to RM
o.append(poly([(310,322),(310,356),(416,356),(416,500),(424,500)], "#6b5bd2", "5,4"))
# RM -> scoreboards
o.append(poly([(760,500),(776,500),(776,60),(790,60)], "#2f6fb5"))
o.append(poly([(776,130),(790,130)], "#2f6fb5"))
o.append(poly([(776,186),(790,186)], "#2f6fb5"))
# RM -> coverage
o.append(poly([(760,530),(772,530),(772,285),(790,285)], "#b83a6a"))
o.append(poly([(632,314),(616,314),(616,450)], "#6b5bd2", "5,4"))  # cache unit agent -> RM
# program item -> RM / stall agent (metadata)
o.append(poly([(22,203),(14,203),(14,362),(416,362)], "#6b5bd2", "5,4", head=False))
# legend
o.append('<rect x="8" y="566" width="904" height="98" rx="6" fill="#fff" stroke="#ccc"/>')
o.append('<text x="22" y="586" font-weight="bold" font-size="10" fill="#333">Legend</text>')
leg=[("#eeeefb","#6b5bd2","Sequences"),("#e1f3ec","#2e9e7c","Input agent"),("#f1efe9","#555","DUT / TB"),("#fbe9e4","#c4573a","Output agents"),("#e6effa","#2f6fb5","Reference model"),("#eaf5df","#5a9a2a","Scoreboards"),("#fbe6ee","#b83a6a","Coverage"),("#fbecd6","#b5772a","Config / checks")]
for i,(f,s,t) in enumerate(leg):
    x=80+i*104
    o.append(f'<rect x="{x}" y="576" width="14" height="12" rx="3" fill="{f}" stroke="{s}"/><text x="{x+20}" y="586" font-size="8.5" fill="#444">{t}</text>')
ll=[("#2e9e7c",None,"Stimulus / APB flow"),("#c4573a",None,"DUT -> output agents"),("#5a9a2a",None,"Agent -> scoreboard"),("#2f6fb5",None,"RM -> scoreboard"),("#6b5bd2","5,4","Streams to RM: APB, program, cache events"),("#d08a00","4,3","Cache Unit stall (signal TBD)"),("#b83a6a",None,"Coverage metadata")]
for i,(c,d,t) in enumerate(ll):
    x=22+(i%4)*224; y=612+(i//4)*22
    dd=f' stroke-dasharray="{d}"' if d else ''
    o.append(f'<line x1="{x}" y1="{y}" x2="{x+34}" y2="{y}" stroke="{c}" stroke-width="1.6"{dd} marker-end="url(#a{c[1:]})"/><text x="{x+42}" y="{y+3}" font-size="8.5" fill="#444">{t}</text>')
o.append('</svg>')
open("env_diagram.svg","w").write("\n".join(o))
