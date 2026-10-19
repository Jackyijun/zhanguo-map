"""把 build/geo.json 与 content/ 的条目注入模板，生成不依赖任何外部文件的 docs/index.html。"""
import json, sys, math
import config as C
sys.path.insert(0, str(C.CONTENT))
import features as F

GEO = json.load(open(C.BUILD / "geo.json", encoding="utf8"))
own = GEO.pop("own")

def dec(fl):
    x = y = 0; out = []
    for i in range(0, len(fl), 2):
        x += fl[i]; y += fl[i + 1]; out.append((x / 100, y / 100))
    return out
def plen(pts):
    return sum(math.hypot((b[0]-a[0])*math.cos(math.radians(a[1])), b[1]-a[1]) for a, b in zip(pts[:-1], pts[1:]))
def midpt(pts, f=0.5):
    L = plen(pts); acc = 0
    for a, b in zip(pts[:-1], pts[1:]):
        d = math.hypot((b[0]-a[0])*math.cos(math.radians(a[1])), b[1]-a[1])
        if acc + d >= L * f and d > 0:
            t = (L * f - acc) / d
            return [round(a[0] + (b[0]-a[0]) * t, 3), round(a[1] + (b[1]-a[1]) * t, 3)]
        acc += d
    return list(pts[len(pts)//2])

I = []
def add(**k):
    k["i"] = len(I); I.append(k); return k

for key, name, surname, prof in F.STATES:
    add(c="state", k=key, old=name, mod=surname, note=prof)
for n, mod, lo, la, st, y0, y1, note in F.CAPITALS:
    add(c="capital", old=n, mod=mod, lon=lo, lat=la, st=st, y0=y0, y1=y1, note=note, tl=own[n + "@" + str(lo)])
for n, mod, lo, la, y, yt, sides, cmd, note in F.BATTLES:
    add(c="battle", old=n, mod=mod, lon=lo, lat=la, y=y, yt=yt, sides=sides, cmd=cmd, note=note, tl=own[n + "@" + str(lo)])
for n, mod, lo, la, note in F.PASSES:
    add(c="pass", old=n, mod=mod, lon=lo, lat=la, note=note, tl=own[n + "@" + str(lo)])
for n, mod, lo, la, note in F.CITIES:
    add(c="city", old=n, mod=mod, lon=lo, lat=la, note=note, tl=own[n + "@" + str(lo)])
for n, mod, lo, la, note in F.TOWNS:
    add(c="town", old=n, mod=mod, lon=lo, lat=la, note=note, tl=own[n + "@" + str(lo)])
for n, mod, lo, la, y, yt, note in F.CULTURE:
    add(c="culture", old=n, mod=mod, lon=lo, lat=la, y=y, yt=yt, note=note, tl=own[n + "@" + str(lo)])
for n, mod, y, yt, note, pts in F.WALLS:
    w = add(c="wall", old=n, mod=mod, y=y, yt=yt, note=note, geo=[[round(a, 3), round(b, 3)] for a, b in pts], anc=midpt(pts))
    if n in F.WALL_END:
        w["y1"] = F.WALL_END[n]
        w["note"] += f"秦统一后废弃（约前{-F.WALL_END[n]}，碣石刻辞“堕坏城郭……夷去险阻”）。"
for n, zhi, mod, lo, la, y0, note in F.JUN:
    add(c="jun", old=n if n == "内史" else (n if n.endswith("郡") else n + "郡"), zhi=zhi, mod=f"郡治 {zhi}（{mod}）", lon=lo, lat=la, y0=y0, k=n, note=note, tl=own["郡:" + n], alias=F.JUN_ALIAS.get(n, ""))
for n, mod, y, yt, note, segs in F.ROADS:
    longest = max(segs, key=plen)
    add(c="road", old=n, mod=mod, y=y, yt=yt, note=note, geo=[[[round(a, 3), round(b, 3)] for a, b in sg] for sg in segs], anc=midpt(longest))
for n, mod, note, w, pts in F.RANGES:
    add(c="range", old=n, mod=mod, note=note, geo=[[round(a, 3), round(b, 3)] for a, b in pts], anc=midpt(pts))

# 水系：按古名归并
RIV_OVERRIDE = {
 "河": ("黄河（下游为战国故道）", "“四渎”之首，战国时单称“河”。下游与今迥异：大致经今浚县宿胥口北流，过内黄、馆陶、临清、德州、沧州，在今黄骅一带入渤海（据谭其骧考订，示意），是齐、赵、燕之间的界河。今河道（虚线）系后世多次改道形成。", [115.65, 36.85]),
 "江": ("长江", None, [114.6, 30.45]),
 "淮水": ("淮河", "“江淮河济”四渎之一。战国时淮河下游经淮阴独流入海，尚无洪泽湖；楚国东进的主轴。", [116.1, 32.45]),
 "治水": ("桑干河·永定河", "又称㶟水，流经代地与燕都蓟南。", None),
 "汉水": ("汉江", None, [111.8, 32.4]),
}
groups = {}
for ri, r in enumerate(GEO["rivers"]):
    if not r.get("n"): continue
    groups.setdefault(r["n"], []).append(ri)
for n, idxs in groups.items():
    rs = [GEO["rivers"][k] for k in idxs]
    mod = rs[0].get("m"); note = next((r.get("note") for r in rs if r.get("note")), "")
    longest = max((dec(r["p"]) for r in rs), key=plen)
    anc = midpt(longest)
    if n in RIV_OVERRIDE:
        m2, n2, a2 = RIV_OVERRIDE[n]
        mod = m2 or mod; note = n2 or note; anc = a2 or anc
    it = add(c="river", sub="river", old=n, mod=mod, note=note, anc=anc)
    for k in idxs: GEO["rivers"][k]["it"] = it["i"]
for ci, cn in enumerate(GEO["canals"]):
    pts = dec(cn["p"])
    it = add(c="river", sub="canal", old=cn["n"], mod=cn["m"], note=cn["note"], anc=midpt(pts))
    cn["it"] = it["i"]
for n, mod, lo, la, rx, ry, note in F.MARSHES:
    add(c="river", sub="marsh", old=n, mod=mod, lon=lo, lat=la, rx=rx, ry=ry, note=note, anc=[lo, la])
for lk in GEO["lakes"]:
    if lk["n"] is None: continue
    if any(x.get("sub") == "lake" and x["old"] == lk["n"] for x in I):
        lk["it"] = next(x["i"] for x in I if x.get("sub") == "lake" and x["old"] == lk["n"]); continue
    it = add(c="river", sub="lake", old=lk["n"], mod=lk["m"], note={"震泽": "即今太湖，又名具区，吴越之间。", "彭蠡泽": "今鄱阳湖前身（古彭蠡泽的范围与今湖不尽相同）。", "巢湖": "楚国江淮之间的大湖。", "洞庭": "《战国策》“楚南有洞庭、苍梧”，战国时湖面远小于后世。", "西海": "青海湖古称，羌人游牧之地。"}.get(lk["n"], ""), anc=lk["c"])
    lk["it"] = it["i"]
for n, lo, la, y0, y1, note in F.PEOPLES:
    add(c="people", old=n, mod="", lon=lo, lat=la, y0=y0, y1=y1, note=note)

DATA = dict(items=I, colors=F.STATE_COLORS, states=[s[0] for s in F.STATES])
html = open(C.ROOT / "src" / "template.html", encoding="utf8").read()
html = html.replace("__GEO__", json.dumps(GEO, ensure_ascii=False, separators=(",", ":")))
html = html.replace("__DATA__", json.dumps(DATA, ensure_ascii=False, separators=(",", ":")))
# 生成配色 CSS
lt = "".join(f"--s-{i}:{c[0]};" for i, (k, c) in enumerate(F.STATE_COLORS.items()))
dk = "".join(f"--s-{i}:{c[1]};" for i, (k, c) in enumerate(F.STATE_COLORS.items()))
html = html.replace("/*__SLIGHT__*/", lt).replace("/*__SDARK__*/", dk)
C.DIST.mkdir(exist_ok=True)
(C.DIST / ".nojekyll").write_text("", encoding="utf8")   # 让 GitHub Pages 原样发布，不经 Jekyll 处理
open(C.DIST / "index.html", "w", encoding="utf8").write(html)
print(len(I), "items;", len(html) // 1024, "KB")
