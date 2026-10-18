"""画几个时间节点的疆域草图，便于检查 seeds.txt 里的归属是否填错。

  python tools/preview.py -350,-284,-260 [西,东,南,北]
输出 build/preview.png（需要 matplotlib）。
"""
import json, sys
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch
from matplotlib.path import Path as MPath
from matplotlib import font_manager

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "content"))
import features as F

for f in font_manager.findSystemFonts():
    if any(k in f for k in ("NotoSansCJK", "NotoSerifCJK", "PingFang", "msyh", "simhei", "Songti", "STHeiti")):
        font_manager.fontManager.addfont(f)
        plt.rcParams["font.family"] = font_manager.FontProperties(fname=f).get_name(); break

D = json.load(open(ROOT / "build" / "geo.json", encoding="utf8"))
def dec(fl):
    x = y = 0; out = []
    for i in range(0, len(fl), 2):
        x += fl[i]; y += fl[i + 1]; out.append((x / 100, y / 100))
    return out

years = [int(a) for a in sys.argv[1].split(",")] if len(sys.argv) > 1 else [-350, -260]
ext = [float(v) for v in sys.argv[2].split(",")] if len(sys.argv) > 2 else [102, 125, 24, 43]
fig, axs = plt.subplots(1, len(years), figsize=(8 * len(years), 7.5))
if len(years) == 1: axs = [axs]
for ax, y in zip(axs, years):
    sn = next(s for s in D["snaps"] if s["y"] == y)
    for p in D["land"]:
        ax.fill(*zip(*dec(p[0])), color="#ECEBE3", ec="#999", lw=.3)
    for k, rings in sn["s"].items():
        col = F.STATE_COLORS[k][0]; verts = []; codes = []
        for r in rings:
            pts = dec(r); verts += pts + [pts[0]]; codes += [MPath.MOVETO] + [MPath.LINETO] * (len(pts) - 1) + [MPath.CLOSEPOLY]
        ax.add_patch(PathPatch(MPath(verts, codes), fc=col, alpha=.55, ec=col, lw=.8))
    for k, L in sn["l"].items():
        for lo, la, sz, rr in L: ax.text(lo, la, k, ha="center", va="center", fontsize=9 + min(10, sz ** .5 / 6))
    for r in D["rivers"]:
        if r["k"] in ("major", "minor"): ax.plot(*zip(*dec(r["p"])), color="#6a8fa8", lw=.6)
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3]); ax.set_aspect(1.25)
    ax.set_title(f"前{-y} {sn['t']}" if y < 0 else f"{y} {sn['t']}")
plt.tight_layout()
out = ROOT / "build" / "preview.png"; plt.savefig(out, dpi=70); print("草图：", out)
