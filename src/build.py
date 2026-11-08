"""计算疆域：读 content/，输出 build/geo.json。"""
import json, math, re, sys
import numpy as np
from shapely.geometry import shape, box, Polygon, MultiPolygon, LineString, MultiLineString, Point
from shapely.ops import unary_union
from scipy import ndimage
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
from skimage import measure, draw
import config as C
sys.path.insert(0, str(C.CONTENT))
import features as F

NE = str(C.NE) + "/"
clipbox = box(*C.BBOX)

def enc_ring(coords, closed=True):
    out = []; px = py = 0
    pts = [(int(round(x * 100)), int(round(y * 100))) for x, y in coords]
    if closed and len(pts) > 1 and pts[0] == pts[-1]: pts = pts[:-1]
    dd = []
    for x, y in pts:
        if dd and (x, y) == (px, py): continue
        dd += [x - px, y - py]; px, py = x, y
    return dd

def polys_of(g):
    if g.is_empty: return []
    if isinstance(g, Polygon): return [g]
    if isinstance(g, MultiPolygon): return list(g.geoms)
    return [p for gg in getattr(g, "geoms", []) for p in polys_of(gg)]

def lines_of(g):
    if g.is_empty: return []
    if isinstance(g, LineString): return [g]
    if isinstance(g, MultiLineString): return list(g.geoms)
    return [l for gg in getattr(g, "geoms", []) for l in lines_of(gg)]

# ---------- 陆地 ----------
land_geoms = []
for fn in ["ne_10m_land.geojson", "ne_10m_minor_islands.geojson"]:
    for f in json.load(open(NE + fn))["features"]:
        g = shape(f["geometry"])
        if not g.intersects(clipbox): continue
        land_geoms.append(g.intersection(clipbox))
land = unary_union(land_geoms)
land_s = land.simplify(C.LAND_SIMPLIFY, preserve_topology=True)
LAND = []
for p in polys_of(land_s):
    if p.area < 0.004: continue
    LAND.append([enc_ring(p.exterior.coords)] + [enc_ring(i.coords) for i in p.interiors if Polygon(i).area > 0.004])
print("land polys", len(LAND), sum(len(r) for p in LAND for r in p) // 2, "pts")

# ---------- 栅格 ----------
RES = C.RES
LON0, LAT0 = C.LON0, C.LAT0
NX, NY = int((C.LON1 - LON0) / RES) + 1, int((C.LAT1 - LAT0) / RES) + 1
lons = LON0 + np.arange(NX) * RES
lats = LAT0 + np.arange(NY) * RES
def to_rc(lon, lat): return (lat - LAT0) / RES, (lon - LON0) / RES

landmask = np.zeros((NY, NX), bool)
for p in polys_of(land):
    for ring, val in [(p.exterior, True)] + [(i, False) for i in p.interiors]:
        xs, ys = np.array(ring.coords).T
        rr, cc = draw.polygon((ys - LAT0) / RES, (xs - LON0) / RES, (NY, NX))
        landmask[rr, cc] = val
print("grid", NX, NY, landmask.mean())

cost = np.where(landmask, 1.0, C.SEA_COST)
rng = np.random.default_rng(C.NOISE_SEED)
noise = ndimage.gaussian_filter(rng.standard_normal((NY, NX)), C.NOISE_SIGMA)
noise /= np.abs(noise).max()
cost *= (1 + C.NOISE_AMP * noise)

def burn(pts, weight, width=1.6):
    m = np.zeros((NY, NX), bool)
    for (a, b), (c, d) in zip(pts[:-1], pts[1:]):
        r0, c0 = to_rc(a, b); r1, c1 = to_rc(c, d)
        n = int(max(abs(r1 - r0), abs(c1 - c0)) * 2) + 2
        for t in np.linspace(0, 1, n):
            r, cc = r0 + (r1 - r0) * t, c0 + (c1 - c0) * t
            rr, ccc = draw.disk((r, cc), width, shape=(NY, NX))
            m[rr, ccc] = True
    return m

for name, mod, note, w, pts in F.RANGES:
    cost[burn(pts, w, C.RANGE_WIDTH)] += w
for rv in F.MANUAL_RIVERS:
    if rv[3] >= 2: cost[burn(rv[4], rv[3], 1.2)] += rv[3] + 1
# 江、汉、漳 作为界河
ne_riv = json.load(open(NE + "ne_10m_rivers_lake_centerlines.geojson"))["features"]
for f in ne_riv:
    nm = f["properties"].get("name")
    if nm in ("Chang Jiang", "Yangtze", "Zhang") and f["geometry"]:
        for l in lines_of(shape(f["geometry"])):
            cost[burn(list(l.coords), C.RIVER_COST, 1.0)] += C.RIVER_COST

import hashlib
COST_SHA = hashlib.sha256(cost.tobytes()).hexdigest()
print("代价栅格", COST_SHA[:16])
if getattr(C, "COST_SHA", None) and C.COST_SHA != COST_SHA[:16]:
    sys.exit(f"代价栅格与约定值 {C.COST_SHA} 不符：春秋、战国两图必须共用同一张代价栅格（山脉、界河、噪声、栅格范围都不能改）")

# ---------- 种子 ----------
# 语法：名称 经度 纬度 初始归属 [年份归属 ...] [~年份]
#   “~-350” 表示该点从前350 起不再参与分区（为前350 以前的小国、戎狄补的点）。
seeds = []
for line in open(C.CONTENT / "seeds.txt", encoding="utf8"):
    line = line.strip()
    if not line or line.startswith("#"): continue
    parts = line.split()
    nm, lo, la = parts[0], float(parts[1]), float(parts[2])
    tl = [[-9999, None if parts[3] == "·" else parts[3]]]
    end = None
    for tok in parts[4:]:
        if tok.startswith("~"):
            end = int(tok[1:]); continue
        m = re.match(r"(-?\d+)(.+)", tok)
        tl.append([int(m.group(1)), None if m.group(2) == "·" else m.group(2)])
    seeds.append(dict(n=nm, lon=lo, lat=la, tl=tl, end=end))
print("seeds", len(seeds), "（其中前350 以前专用", sum(s["end"] is not None for s in seeds), "）")
def owner(tl, y):
    o = None
    for t, s in tl:
        if y >= t: o = s
    return o

# ---------- 多源最短路 ----------
idx = np.arange(NY * NX).reshape(NY, NX)
coslat = np.cos(np.radians(lats))[:, None] * np.ones((1, NX))
rows, cols, ws = [], [], []
for dr, dc in [(0, 1), (1, 0), (1, 1), (1, -1)]:
    r0 = slice(0, NY - dr); r1 = slice(dr, NY)
    if dc >= 0: c0 = slice(0, NX - dc); c1 = slice(dc, NX)
    else: c0 = slice(-dc, NX); c1 = slice(0, NX + dc)
    a = idx[r0, c0].ravel(); b = idx[r1, c1].ravel()
    step = np.sqrt((dc * coslat[r0, c0]) ** 2 + dr ** 2).ravel()
    w = 0.5 * (cost[r0, c0].ravel() + cost[r1, c1].ravel()) * step
    rows += [a, b]; cols += [b, a]; ws += [w, w]
G = coo_matrix((np.concatenate(ws), (np.concatenate(rows), np.concatenate(cols))), shape=(NY * NX, NY * NX)).tocsr()
sidx = []
for s in seeds:
    r, c = to_rc(s["lon"], s["lat"])
    sidx.append(idx[int(round(r)), int(round(c))])
dup = [s["n"] for s, v in zip(seeds, sidx) if sidx.count(v) > 1]
assert not dup, f"归属点重格：{dup}"

# 每个节点只用当年仍参与分区的点；同一组点只算一次
_parts = {}
def partition(y):
    act = tuple(i for i, s in enumerate(seeds) if s["end"] is None or y < s["end"])
    if act not in _parts:
        _, _, src = dijkstra(G, indices=[sidx[i] for i in act], min_only=True, return_predecessors=True)
        pos = {sidx[i]: i for i in act}
        lut = np.full(NY * NX, -1, dtype=np.int32)
        for v, i in pos.items(): lut[v] = i
        src = src.ravel()
        lab = np.where(src >= 0, lut[np.maximum(src, 0)], -1).reshape(NY, NX)
        _parts[act] = lab
        print("   分区", len(act), "点")
    return _parts[act]
LATE = max([s["end"] for s in seeds if s["end"] is not None], default=-9999)
label = partition(max(LATE, F.SNAPS[-1][0]))     # 秦郡与点要素归属沿用最后一期的分区
print("labelled")

# ---------- 快照 ----------
STATE_KEYS = [s[0] for s in F.STATES]
SN = []
for (y, title, desc) in F.SNAPS:
    own = np.array([STATE_KEYS.index(owner(s["tl"], y)) if owner(s["tl"], y) else -1 for s in seeds] + [-1])
    omap = own[partition(y)]
    shapes, labs = {}, {}
    for k, key in enumerate(STATE_KEYS):
        m = omap == k
        if not m.any(): continue
        sm = ndimage.gaussian_filter(m.astype(float), C.SMOOTH_SIGMA)
        pad = np.pad(sm, 1)
        rings = []
        for cnt in measure.find_contours(pad, 0.5):
            cnt = cnt - 1
            pts = [(LON0 + c * RES, LAT0 + r * RES) for r, c in cnt]
            if len(pts) < 4: continue
            ls = LineString(pts).simplify(C.POLY_SIMPLIFY)
            if Polygon(ls.coords).area < C.MIN_RING_AREA: continue
            rings.append(enc_ring(list(ls.coords)))
        shapes[key] = rings
        # 注记位置：陆地上的最大连通块
        ml = m & landmask
        lab, n = ndimage.label(ml)
        if n == 0: continue
        sizes = ndimage.sum(ml, lab, range(1, n + 1))
        order = np.argsort(-sizes)
        L = []
        for j in order[:3]:
            if sizes[j] < max(40, sizes[order[0]] * 0.3) and j != order[0]: continue
            comp = lab == j + 1
            dt = ndimage.distance_transform_edt(np.pad(comp, 1))[1:-1, 1:-1]
            r, c = np.unravel_index(np.argmax(dt), dt.shape)
            L.append([round(LON0 + c * RES, 2), round(LAT0 + r * RES, 2), int(sizes[j]), round(float(dt.max()) * RES, 2)])
        labs[key] = L
    SN.append(dict(y=y, t=title, d=desc, s=shapes, l=labs))
    print(y, {k: len(v) for k, v in shapes.items()})

# ---------- 秦郡：在秦境内按郡治就近分区 ----------
def seed_tl_at(lon, lat):
    r, c = to_rc(lon, lat)
    r = min(max(int(round(r)), 0), NY - 1); c = min(max(int(round(c)), 0), NX - 1)
    k = label[r, c]
    return seeds[k]["tl"] if k >= 0 else [[-9999, None]]

JUN = getattr(F, "JUN", [])
QIN = STATE_KEYS.index("秦") if "秦" in STATE_KEYS else -1
jcell = []
for j in JUN:
    r, c = to_rc(j[3], j[4]); jcell.append(idx[int(round(r)), int(round(c))])
assert len(set(jcell)) == len(jcell), "郡治重格"
jcache = {}
for sn, (y, title, desc) in zip(SN, F.SNAPS):
    act = tuple(k for k, j in enumerate(JUN) if j[5] <= y and owner(seed_tl_at(j[3], j[4]), y) in ("秦", "卫"))
    own = np.array([STATE_KEYS.index(owner(s["tl"], y)) if owner(s["tl"], y) else -1 for s in seeds] + [-1])
    qin = own[partition(y)] == QIN
    if not act or not qin.any(): sn["j"] = {}; continue
    if act not in jcache:
        _, _, jsrc = dijkstra(G, indices=[jcell[k] for k in act], min_only=True, return_predecessors=True)
        pos = {jcell[k]: k for k in act}
        jcache[act] = np.vectorize(lambda v: pos.get(v, -1))(jsrc.reshape(NY, NX))
    jl = jcache[act]
    jr = {}
    for k in act:
        m = qin & (jl == k)
        if m.sum() < 6: continue
        sm = ndimage.gaussian_filter(m.astype(float), C.SMOOTH_SIGMA)
        rings = []
        for cnt in measure.find_contours(np.pad(sm, 1), 0.5):
            cnt = cnt - 1
            pts = [(LON0 + c * RES, LAT0 + r * RES) for r, c in cnt]
            if len(pts) < 4: continue
            ls = LineString(pts).simplify(C.POLY_SIMPLIFY)
            if Polygon(ls.coords).area < C.MIN_RING_AREA: continue
            rings.append(enc_ring(list(ls.coords)))
        if rings: jr[JUN[k][0]] = rings
    sn["j"] = jr
    print(y, "郡", len(jr))

# ---------- 河流 ----------
RIV = []
for f in ne_riv:
    p = f["properties"]; nm = p.get("name")
    if not f["geometry"]: continue
    g = shape(f["geometry"])
    if not g.intersects(clipbox): continue
    if p.get("featurecla") == "Lake Centerline" and nm not in ("Gan", "Yuan"): continue
    if nm in ("Hudi", "Huang", "Min", "Quan", "Ying", "Hai", "Jinsha", "Tongtian", "Zi") and nm != "Huang":
        if nm in ("Hudi", "Quan", "Ying", "Hai", "Tongtian", "Zi"): continue
        if nm == "Min" and g.bounds[0] < 110: continue
    for l in lines_of(g.intersection(clipbox)):
        ls = l.simplify(0.01)
        if nm == "Huang":
            # 以 113.1°E 为界：以西为“河”，以东为今黄河下游（古今异道）
            west = ls.intersection(box(90, 20, 113.1, 46)); east = ls.intersection(box(113.1, 20, 130, 46))
            for part in lines_of(west): RIV.append(dict(n="河", m="黄河", k="major", p=enc_ring(list(part.coords), False)))
            for part in lines_of(east): RIV.append(dict(n=None, m="今黄河下游", k="modern", p=enc_ring(list(part.coords), False)))
            continue
        if nm in F.NE_RIVERS:
            a, mo, note = F.NE_RIVERS[nm]
            kind = "major" if nm in ("Chang Jiang", "Yangtze", "Huai") else "minor"
            RIV.append(dict(n=a, m=mo, k=kind, note=note, p=enc_ring(list(ls.coords), False)))
        elif nm in F.NE_RIVERS_MINOR or nm is None:
            if ls.length < 0.4: continue
            RIV.append(dict(n=None, m=None, k="faint", p=enc_ring(list(ls.coords), False)))
for (a, mo, note, w, pts, kind) in F.MANUAL_RIVERS:
    RIV.append(dict(n=a, m=mo, k=kind, note=note, p=enc_ring(pts, False)))
CAN = []
for cn in F.CANALS:          # (名, 今名, 注, 点列) 或 (名, 今名, 开凿年, 注, 点列)
    a, mo, *mid, pts = cn
    d = dict(n=a, m=mo, note=mid[-1], p=enc_ring(pts, False))
    if len(mid) == 2: d["y"] = mid[0]
    CAN.append(d)

LAK = []
for f in json.load(open(NE + "ne_10m_lakes.geojson"))["features"]:
    nm = f["properties"].get("name")
    if nm not in F.NE_LAKES or not f["geometry"]: continue
    g = shape(f["geometry"]).simplify(0.01)
    for p in polys_of(g):
        c = p.representative_point()
        a, mo = F.NE_LAKES[nm]
        LAK.append(dict(n=a, m=mo, c=[round(c.x, 2), round(c.y, 2)], r=enc_ring(p.exterior.coords)))

# ---------- 今省界（简化，已预先编码） ----------
PROV = json.load(open(C.GEODATA / "prov.json", encoding="utf8"))

# ---------- 点要素所在种子 ----------
# 分区随年代可能不同（前350 起部分点退出），点要素的归属沿革按各段分区拼接
_starts = [-9999] + sorted({s["end"] for s in seeds if s["end"] is not None})
def seed_at(lon, lat):
    r, c = to_rc(lon, lat)
    r = min(max(int(round(r)), 0), NY - 1); c = min(max(int(round(c)), 0), NX - 1)
    out = []
    for i, y0 in enumerate(_starts):
        y1 = _starts[i + 1] if i + 1 < len(_starts) else 10 ** 6
        k = partition(y0)[r, c]
        tl = seeds[k]["tl"] if k >= 0 else [[-9999, None]]
        for t, o in [[y0, owner(tl, y0)]] + [[t, o] for t, o in tl if y0 < t < y1]:
            if not out or out[-1][1] != o: out.append([t, o])
    return out

def tl_str(tl): return ";".join(f"{t}:{s or ''}" for t, s in tl)

OUT = dict(land=LAND, prov=PROV, rivers=RIV, canals=CAN, lakes=LAK, snaps=SN)
if getattr(F, "FIRST", None) is not None: OUT["first"] = F.FIRST     # 首屏节点年份
pts_owner = {}
for grp in (F.CAPITALS, F.CITIES, F.PASSES, F.BATTLES, F.CULTURE, F.TOWNS):
    for it in grp:
        pts_owner[it[0] + "@" + str(it[2])] = tl_str(seed_at(it[2], it[3]))
for it in JUN:
    pts_owner["郡:" + it[0]] = tl_str(seed_at(it[3], it[4]))
OUT["own"] = pts_owner
C.BUILD.mkdir(exist_ok=True)
json.dump(OUT, open(C.BUILD / "geo.json", "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
print("geo.json", (C.BUILD / "geo.json").stat().st_size // 1024, "KB")
