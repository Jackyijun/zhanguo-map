# 战国列国形势图

战国中后期（前350—前221）的交互历史地图：36 个时间节点的列国疆域，16 国（七雄之外还有周、宋、卫、鲁、中山、越、巴、蜀、义渠），200 多处都城、城邑、关隘的古今地名对照，以及战役、变法与工程、长城、山川、周边诸族。

---

## 一、直接看

双击 **`docs/index.html`**，用任意现代浏览器（Chrome、Edge、Safari、Firefox）打开即可。

这个文件约 450 KB，数据、样式、脚本全部内嵌：不联网、不需要服务器、不依赖任何外部库。可以直接拷到 U 盘、发给别人，或者放到自己的网站上。

---

## 二、放到网上（GitHub Pages）

1. 把整个项目推到 GitHub 仓库（例如 `zhanguo-map`）。
2. 在仓库的 **Settings → Pages** 里：
   - Source 选 **Deploy from a branch**；
   - Branch 选 **main**，目录选 **/docs**，保存。
3. 一两分钟后，网页就会出现在 `https://<你的用户名>.github.io/zhanguo-map/`。

`docs/.nojekyll` 是一个空文件，作用是让 GitHub Pages 原样发布 `docs/` 里的文件，不经过 Jekyll 处理。

以后每次修改，运行 `python run.py`，把 `docs/index.html` 一起提交推送，网页就会自动更新。

也可以上传到 Netlify、Cloudflare Pages 或任何网页空间。

---

## 三、本地重新构建

改了史料内容（`content/`）或参数（`src/config.py`）之后才需要重新构建。需要 **Python 3.9 或更新版本**。

**macOS / Linux**

```bash
cd zhanguo-map
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py --open
```

**Windows（PowerShell）**

```powershell
cd zhanguo-map
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py --open
```

完整构建约 30 秒，完成后会用浏览器打开新生成的 `docs/index.html`。

| 命令 | 作用 |
|---|---|
| `python run.py` | 底图缺失则下载 → 计算疆域 → 拼装 HTML |
| `python run.py --html` | 只重新拼装 HTML（只改了 `src/template.html`，或 `content/features.py` 里的文字时用，不到 1 秒） |
| `python run.py --open` | 构建完后在浏览器中打开 |
| `python run.py --preview -350,-260` | 额外画出这几个节点的疆域草图到 `build/preview.png`，便于检查归属是否填错 |
| `python tools/preview.py -284 113,123,33,41` | 只画草图，可指定经纬范围（西,东,南,北） |

项目里已经带了底图数据（`geodata/ne/`，约 23 MB），离线也能构建。如果删掉了，`run.py` 会自动从 GitHub 下载固定版本（Natural Earth v5.1.2）。

同一份输入，构建结果逐字节一致，可以用 git 追踪改动。

---

## 四、目录结构

```
zhanguo-map/
├── run.py                 一键构建入口
├── requirements.txt
├── docs/
│   ├── index.html         ★ 成品，单文件（GitHub Pages 从这里发布）
│   └── .nojekyll          让 GitHub Pages 原样发布
├── content/               ★ 史料内容（手写，主要改这里）
│   ├── seeds.txt          365 个归属点：地名、经纬度、哪年归哪国
│   └── features.py        列国介绍与配色、36 个时间节点、国都、战役、关隘、
│                          名城、一般城邑、变法工程、山脉、水系、湖泽、长城、诸族
├── src/
│   ├── config.py          ★ 全部路径与可调参数（栅格、代价、平滑……）
│   ├── fetch_data.py      下载 Natural Earth 底图
│   ├── build.py           计算疆域，输出 build/geo.json
│   ├── assemble.py        把数据注入模板，输出 docs/index.html
│   └── template.html      前端：页面结构、样式、交互脚本
├── geodata/
│   ├── prov.json          今省界（简化，已编码）
│   └── ne/                Natural Earth 1:10m GeoJSON（陆地、小岛、河流、湖泊）
├── tools/
│   └── preview.py         matplotlib 疆域草图
└── build/                 中间产物（可随时删除）
```

---

## 五、工作原理

```
content/seeds.txt ──┐
content/features.py ┼─► build.py ─► build/geo.json ─► assemble.py ─► docs/index.html
geodata/ (底图) ────┘                                    ▲
                                       content/features.py + src/template.html
```

### 1. 为什么疆域要“算”出来

战国没有现成的边界数据。史书能确定的大多是“某年某城归某国”。所以这里的做法是：

1. 只手写**地点 → 国家**的归属及其变化年份（`seeds.txt`）；
2. 用一张“通行代价”地图让计算机推出国与国之间的分界，让分界尽量落在山脊和大河上。

### 2. `build.py` 的步骤

1. **陆地**：从 Natural Earth 裁出东亚陆地，简化后编码。
2. **代价栅格**：0.05° 一格。陆地代价 1，海 4.5；`features.py` 里每条山脉按其“阻隔权重”加代价，古黄河、济水、易水、北洛水和江、汉、漳也加代价；再叠一层固定随机种子的平滑噪声，让界线略带自然弯曲。
3. **多源最短路**：从 365 个归属点同时出发做 Dijkstra，每一格归给“走过去最近”的那个点。这一步只做一次。
4. **逐节点着色**：对每个时间节点，按 `seeds.txt` 查出每个点当年属哪国，把格子合并成各国范围，高斯平滑后描出轮廓并简化。注记位置取每国最大一块陆地的内部最远点。
5. **水系与湖泽**：Natural Earth 河流按英文名对到古名；战国黄河故道、济水、北洛水、伊洛、汝颍、泗水、滹沱、易水等手绘补上。今黄河下游另画一条虚线以示古今改道。
6. **地点归属**：每个城邑、关隘、战役点查它落在哪个归属点的格子里，带上那个点的归属变化，供提示框显示“某年属某国”。

### 3. `seeds.txt` 语法

每行一个点：

```
名称 经度 纬度 初始归属 [年份归属 ...]
```

- `·` 表示不属任何诸侯国（戎狄蛮夷之地）。
- 年份用负数表示公元前，`-330秦` 表示前330 年起属秦。

例：

```
少梁 110.45 35.57 魏 -330秦
长平 112.92 35.8 韩 -262赵 -260秦 -257赵 -247秦
野王 112.93 35.09 韩 -262秦 -241卫 -209秦
会稽 120.58 30.0 越 -306· -222秦
```

改了 `seeds.txt` 或 `features.py` 里的时间节点、山脉、手绘河流之后，要完整运行 `python run.py`。只改说明文字，`python run.py --html` 就够了。

### 4. `features.py` 里有什么

| 名称 | 内容 |
|---|---|
| `STATES` · `STATE_COLORS` | 16 国的姓氏、介绍，以及浅色 / 深色两套疆域色 |
| `SNAPS` | 36 个时间节点：年份、标题、一段概述 |
| `CAPITALS` | 36 处国都，含起止年份（迁都后旧都显示为虚线框） |
| `BATTLES` | 36 场战役：年份、胜负、主将、经过 |
| `PASSES` · `CITIES` · `TOWNS` | 20 处关隘津渡、26 座名城要邑、145 座一般城邑 |
| `CULTURE` | 19 处变法、学术、工程与考古遗址 |
| `WALLS` · `RANGES` | 9 段长城、24 条山脉 |
| `NE_RIVERS` · `MANUAL_RIVERS` · `CANALS` · `MARSHES` · `NE_LAKES` | 水系古名、手绘河道、运河、古泽薮、湖泊 |
| `PEOPLES` | 18 处周边诸族注记，按存续年份显示 |

### 5. 前端显示规则

- 战役、变法与工程、长城只显示到当前节点为止已经发生的；国都只显示当时的国都和已废的旧都。
- 在索引、年表、对照表里点开一个“未来”的事件，时间轴会自动跳到它之后最近的节点。
- 缩放分级：全图只显示国名、国都、战役和关隘；放大后才出现名城、一般城邑和今名。

---

## 六、资料与可靠程度

- **疆域归属**：依据《史记》《战国策》《竹书纪年》等史料与谭其骧《中国历史地图集》第一册战国图的大意推定，由 AI 协助编写，未逐条核对原文。大的格局和关键年份（如前330 魏献河西、前316 灭巴蜀、前284 乐毅破齐、前260 长平、前230—前221 秦灭六国）比较可靠；某城某年的具体归属、边缘地区（辽东、岭南、西南夷）的范围较粗略。
- **边界线**：完全是推算的示意线，只表示“这一带属于这个国家”，不代表史书里有这样一条界线。
- **有争议处**：地图里注明“一说”，如马陵、阏与、中牟、巨阳的地望；越国灭亡采用杨宽的约前306 说，传统说为前334/前333。
- **底图**：Natural Earth 1:10m（公有领域）；今省界沿用自作者此前的另一张地图。

有错欢迎指正。

---

## 七、调参

所有可调参数都在 `src/config.py`：

| 参数 | 作用 |
|---|---|
| `RES` | 栅格边长。改小更细，但计算更慢 |
| `SEA_COST` | 跨海代价。调大可防止疆域隔海相连 |
| `NOISE_SEED` · `NOISE_AMP` | 界线弯曲的随机种子与幅度 |
| `RANGE_WIDTH` · `RIVER_COST` | 山脊阻隔带宽度、界河代价 |
| `SMOOTH_SIGMA` · `POLY_SIMPLIFY` | 轮廓平滑程度与简化容差 |

山脉的阻隔强度在 `features.py` 的 `RANGES` 里逐条设置（第 4 个字段）。
