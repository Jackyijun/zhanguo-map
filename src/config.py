"""全部路径与可调参数。"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"          # 史料内容（手写）
GEODATA = ROOT / "geodata"          # 底图数据
NE = GEODATA / "ne"                 # Natural Earth 1:10m GeoJSON
BUILD = ROOT / "build"              # 中间产物（可随时删除）
DIST = ROOT / "docs"                # 成品：docs/index.html（GitHub Pages 可直接从 /docs 发布）

# Natural Earth 固定版本（与仓库内 geodata/ne/ 完全一致）
NE_TAG = "v5.1.2"
NE_FILES = ["ne_10m_land", "ne_10m_minor_islands", "ne_10m_rivers_lake_centerlines", "ne_10m_lakes"]

# 底图裁剪范围（西, 南, 东, 北）
BBOX = (96.0, 20.0, 129.0, 45.5)
LAND_SIMPLIFY = 0.012               # 海岸线简化容差（度）

# 疆域分区栅格
RES = 0.05                          # 栅格边长（度）
LON0, LAT0, LON1, LAT1 = 97.0, 21.0, 128.5, 44.5
SEA_COST = 4.5                      # 跨海代价（陆地为 1）
NOISE_SEED, NOISE_SIGMA, NOISE_AMP = 7, 6, 0.45   # 让界线略带自然弯曲
RANGE_WIDTH = 2.2                   # 山脊阻隔带半宽（格）
RIVER_COST = 3                      # 江、汉、漳等界河的附加代价

# 疆域多边形平滑与简化
SMOOTH_SIGMA = 1.1
POLY_SIMPLIFY = 0.018
MIN_RING_AREA = 0.01
