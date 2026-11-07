# 战国列国形势图

[![中文](https://img.shields.io/badge/lang-%E4%B8%AD%E6%96%87-red.svg)](README.md) [![English](https://img.shields.io/badge/lang-English-blue.svg)](README.en.md)

战国中后期至秦统一后的极盛（前350—前212）的交互历史地图：37 个时间节点的列国疆域，17 国（七雄之外还有周、宋、卫、鲁、中山、越、巴、蜀、苴、义渠），200 多处都城、城邑、关隘的古今地名对照，秦郡的逐步设置，以及战役、事件与工程、长城、驰道直道、山川、周边诸族。界面中英双语，地图右上角「中 | EN」切换。

---

## 一、直接看

双击 **`docs/index.html`**，用任意现代浏览器（Chrome、Edge、Safari、Firefox）打开即可。

这个文件约 730 KB，数据、样式、脚本全部内嵌：不联网、不需要服务器、不依赖任何外部库。可以直接拷到 U 盘、发给别人，或者放到自己的网站上。

---

## 二、线上地址

https://jackyijun.github.io/zhanguo-map/

---

## 三、本地构建

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
| `python run.py --html` | 只重新拼装 HTML（只改了 `src/template.html`、`content/features.py` 里的文字或 `content/en/` 的英文时用，不到 1 秒） |
| `python run.py --draft` | 英文有缺译或过期时也照样出图（缺译处临时显示中文），只供预览；不加时构建会停下并列出缺译 |
| `python run.py --open` | 构建完后在浏览器中打开 |
| `python run.py --preview -350,-260` | 额外画出这几个节点的疆域草图到 `build/preview.png`，便于检查归属是否填错 |
| `python tools/preview.py -284 113,123,33,41` | 只画草图，可指定经纬范围（西,东,南,北） |

项目里已经带了底图数据（`geodata/ne/`，约 23 MB），离线也能构建。如果删掉了，`run.py` 会自动从 GitHub 下载固定版本（Natural Earth v5.1.2）。

同一份输入，构建结果逐字节一致，可以用 git 追踪改动。

构建完成后，把 docs/index.html 一起提交并推送到 main，线上网页会自动更新。

---

## 四、目录结构

```
zhanguo-map/
├── run.py                 一键构建入口
├── requirements.txt
├── docs/
│   ├── index.html         ★ 成品，单文件（GitHub Pages 从这里发布）
│   └── .nojekyll          让 GitHub Pages 原样发布
├── README.md · README.en.md   中文说明 · 英文说明
├── content/               ★ 史料内容（手写，主要改这里）
│   ├── seeds.txt          386 个归属点：地名、经纬度、哪年归哪国
│   ├── features.py        列国介绍与配色、37 个时间节点与时间轴短名、国都、战役、
│   │                      关隘、名城、一般城邑、事件工程、山脉、水系、湖泽、长城、
│   │                      诸族、秦郡、驰道直道、年表里的灭国条目
│   └── en/                英文译文
│       ├── items.json     条目（国、都、战役、城邑、山川……）
│       ├── snaps.json     时间节点的标题、短名、概述
│       ├── misc.json      今省名、灭国条目
│       ├── zh.lock.json   每条英文所据中文的指纹
│       └── GLOSSARY.md    译名体例
├── src/
│   ├── config.py          ★ 全部路径与可调参数（栅格、代价、平滑……）
│   ├── fetch_data.py      下载 Natural Earth 底图
│   ├── build.py           计算疆域，输出 build/geo.json
│   ├── assemble.py        并入英文、检查缺译，把数据注入模板，输出 docs/index.html
│   ├── i18n.py            英文版的公共部分：待译字段清单、指纹
│   └── template.html      前端：页面结构、样式、交互脚本（含中英界面文字）
├── geodata/
│   ├── prov.json          今省界（简化，已编码）
│   └── ne/                Natural Earth 1:10m GeoJSON（陆地、小岛、河流、湖泊）
├── tools/
│   ├── preview.py         matplotlib 疆域草图
│   └── i18n.py            英文维护：status · todo · lock · table
└── build/                 中间产物（可随时删除）
```

---

## 五、工作原理

```
content/seeds.txt ──┐
content/features.py ┼─► build.py ─► build/geo.json ─► assemble.py ─► docs/index.html
geodata/ (底图) ────┘                                    ▲
                          content/features.py + content/en/ + src/template.html
```

### 1. 为什么疆域要“算”出来

战国没有现成的边界数据。史书能确定的大多是“某年某城归某国”。所以这里的做法是：

1. 只手写**地点 → 国家**的归属及其变化年份（`seeds.txt`）；
2. 用一张“通行代价”地图让计算机推出国与国之间的分界，让分界尽量落在山脊和大河上。

### 2. `build.py` 的步骤

1. **陆地**：从 Natural Earth 裁出东亚陆地，简化后编码。
2. **代价栅格**：0.05° 一格。陆地代价 1，海 4.5；`features.py` 里每条山脉按其“阻隔权重”加代价，古黄河、济水、易水、北洛水和江、汉、漳也加代价；再叠一层固定随机种子的平滑噪声，让界线略带自然弯曲。
3. **多源最短路**：从 386 个归属点同时出发做 Dijkstra，每一格归给“走过去最近”的那个点。这一步只做一次。
4. **逐节点着色**：对每个时间节点，按 `seeds.txt` 查出每个点当年属哪国，把格子合并成各国范围，高斯平滑后描出轮廓并简化。注记位置取每国最大一块陆地的内部最远点。
5. **秦郡**：对每个节点，取当时已经设置、且郡治在秦境内的郡，以各郡治为源点在同一张代价图上再做一次多源最短路，把秦境划分给各郡，描出郡界。郡界因此只是“就近归郡”的推算，不是史载的郡界。
6. **水系与湖泽**：Natural Earth 河流按英文名对到古名；战国黄河故道、济水、北洛水、伊洛、汝颍、泗水、滹沱、易水等手绘补上。今黄河下游另画一条虚线以示古今改道。
7. **地点归属**：每个城邑、关隘、战役点查它落在哪个归属点的格子里，带上那个点的归属变化，供提示框显示“某年属某国”。

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
| `STATES` · `STATE_COLORS` | 17 国的姓氏、介绍，以及浅色 / 深色两套疆域色 |
| `SNAPS` · `SNAP_SHORT` | 37 个时间节点：年份、标题、一段概述（最后一个是前212“疆域极盛”）；时间轴上竖排的短名 |
| `CAPITALS` | 37 处国都，含起止年份（迁都后旧都显示为虚线框） |
| `BATTLES` | 43 场战役：年份、胜负、主将、经过（含秦统一后的南征百越、北击匈奴） |
| `PASSES` · `CITIES` · `TOWNS` | 20 处关隘津渡、28 座名城要邑、145 座一般城邑 |
| `CULTURE` | 27 处事件、变法、学术、工程与考古遗址（含灵渠、阿房宫、焚书坑儒等） |
| `WALLS` · `WALL_END` · `RANGES` | 10 段长城（含秦始皇新筑段）、统一后废弃的内地长城、24 条山脉 |
| `NE_RIVERS` · `MANUAL_RIVERS` · `CANALS` · `MARSHES` · `NE_LAKES` | 水系古名、手绘河道、运河、古泽薮、湖泊 |
| `PEOPLES` | 18 处周边诸族注记，按存续年份显示 |
| `JUN` · `JUN_ALIAS` | 51 个秦郡（含内史）：郡治、今地、设置年份、说明，以及供检索的别称（如临菑郡＝齐郡） |
| `ROADS` | 驰道、直道、五尺道的走向（示意）与年份 |
| `FALLS` | 年表里的灭国条目：年份、亡国名、经过 |

### 5. 前端显示规则

- 战役只显示**本期**的，即上一个节点之后（不含）到本节点（含）发生的；说明栏末尾列出“本期战役”，点击即定位。右侧列表里本期战役排在最前，其余变灰，悬停时地图上淡显。
- 事件与工程、长城、驰道直道只显示到当前节点为止已经发生的；国都只显示当时的国都和已废的旧都。
- 秦统一后废弃的六国内地长城（魏、赵南、燕南、齐长城与楚方城），从前212 节点起淡显，并在名称后加“（废）”。
- 秦郡只显示当时已经设置、且郡治在秦境内的郡：郡界为虚线，郡治为双环符号。图例里可单独关掉“秦郡”。
- 在索引、年表、对照表里点开一场其他时期的战役，时间轴会跳到它所在的那一期；点开一个“未来”的事件，会跳到它之后最近的节点。
- 缩放分级：全图只显示国名、国都、战役和关隘；放大后才出现名城、一般城邑和今名。

---

## 六、常见修改

| 想做的事 | 改哪里 | 之后运行 |
|---|---|---|
| 改某城某年的归属 | `content/seeds.txt` 对应一行（语法见上节） | `python run.py` |
| 加一个城邑、关隘、战役、事件 | `content/features.py` 对应列表加一行；若想让它影响疆域，再在 `seeds.txt` 加归属点 | 只改 `features.py`：`python run.py --html`；动了 `seeds.txt`：`python run.py` |
| 加一个时间节点 | `features.py` 的 `SNAPS` 加一行（年份、标题、概述），`SNAP_SHORT` 加时间轴短名 | `python run.py` |
| 改说明文字 | `features.py` 里的按语、节点概述 | `python run.py --html`（会提示对应英文过期，见下节） |
| 改英文 | `content/en/*.json` | `python tools/i18n.py lock` → `python run.py --html` |
| 改配色 | `features.py` 的 `STATE_COLORS`（浅色、深色两值） | `python run.py --html` |
| 改界面文字 | `src/template.html` 里的 `U`（`zh`、`en` 两套） | `python run.py --html` |

改完中文、补上英文之后，`python tools/i18n.py status` 应显示缺译、过期都是 0，严格构建才能通过。

---

## 七、英文版

同一个 `docs/index.html` 里有中、英两种界面，默认中文；地图右上角「中 | EN」切换，选择记在浏览器里，网址加 `#en` 直接打开英文。英文模式下地图只标英文，悬停说明、索引、年表、对照表在英文名后附小号汉字原名；检索同时收中英文，英文不分大小写。

- **中文是源文本。** 英文按“文件 · 键 · 字段”另存在 `content/en/`：条目键为 `类别:古名`（同类同名的第二条起加 `#2`），节点键为年份，今省名为 `prov:省名`，灭国条目为 `fall:年份`。
- **指纹。** `zh.lock.json` 记下每条英文所据中文的 sha1 前 10 位。中文一改，对应英文就算“过期”；`assemble.py` 默认严格，有缺译或过期就停下，`--draft` 才放行。
- **工具。** `python tools/i18n.py status` 看缺译、过期条数；`todo` 把待译的中文导出到 `build/i18n_todo.json`；`table` 导出中英对照表 `build/i18n_table.csv`（Excel 可直接打开）供审校；`lock` 登记指纹。`names` / `notes` 参数可只看名称层或按语层。
- **译名体例**见 `content/en/GLOSSARY.md`：拼音写法、卫作 Wey、通名（Pass、Ford、Commandery、Long Wall……）、今地写法、年代写法等。

---

## 八、调参

所有可调参数都在 `src/config.py`：

| 参数 | 作用 |
|---|---|
| `RES` | 栅格边长。改小更细，但计算更慢 |
| `SEA_COST` | 跨海代价。调大可防止疆域隔海相连 |
| `NOISE_SEED` · `NOISE_AMP` | 界线弯曲的随机种子与幅度 |
| `RANGE_WIDTH` · `RIVER_COST` | 山脊阻隔带宽度、界河代价 |
| `SMOOTH_SIGMA` · `POLY_SIMPLIFY` | 轮廓平滑程度与简化容差 |

山脉的阻隔强度在 `features.py` 的 `RANGES` 里逐条设置（第 4 个字段）。

---

## 九、资料与可靠程度

- **疆域归属**：依据《史记》《战国策》《竹书纪年》等史料与谭其骧《中国历史地图集》第一册战国图的大意推定，由 AI 协助编写，未逐条核对原文。大的格局和关键年份（如前330 魏献河西、前316 灭巴蜀、前284 乐毅破齐、前260 长平、前230—前221 秦灭六国）比较可靠；某城某年的具体归属、边缘地区（辽东、岭南、西南夷）的范围较粗略。
- **边界线**：完全是推算的示意线，只表示“这一带属于这个国家”，不代表史书里有这样一条界线。
- **秦郡**：《史记》只说“分天下以为三十六郡”，没有列出郡名。郡目与郡治主要依后晓荣《秦代政区地理》（2009）的五十四郡说，参照《汉书·地理志》《水经注》、秦封泥与岳麓书院秦简、里耶秦简；其中治所不明的新秦中、胶西、河间、巫黔四郡没有画，苍梧郡治所未详，位置为推测。统一后才析置的郡（济北、即墨、城阳、博阳、东海、河内、清河、衡山）设置年暂记为前220，只在前212 节点出现。郡界由郡治就近推算，不是史载郡界，沿海的郡界裁到海岸线为止。
- **有争议处**：地图里注明“一说”，如马陵、阏与、中牟、巨阳的地望；越国灭亡采用杨宽的约前306 说，传统说为前334/前333。
- **英文**：译名与按语由 AI 翻译，经独立复核；体例见 `content/en/GLOSSARY.md`。英文与中文不一致时以中文为准。
- **底图**：Natural Earth 1:10m（公有领域）；今省界沿用自作者此前的另一张地图。

有错欢迎指正。
