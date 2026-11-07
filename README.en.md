# The Warring States

[![中文](https://img.shields.io/badge/lang-%E4%B8%AD%E6%96%87-red.svg)](README.md) [![English](https://img.shields.io/badge/lang-English-blue.svg)](README.en.md)

An interactive historical map of the later Warring States period through the Qin empire at its greatest extent (350–212 BC): the territories of the states at 37 points in time; 17 states (besides the seven powers, Zhou, Song, Wey, Lu, Zhongshan, Yue, Ba, Shu, Ju and Yiqu); ancient and modern names for more than 200 capitals, cities, towns and passes; the step-by-step creation of the Qin commanderies; and battles, events and public works, long walls, the imperial highways and the Straight Road, mountains and rivers, and the neighbouring peoples. The interface is bilingual: switch with the "中 | EN" control at the top right of the map.

---

## 1. Just open it

Double-click **`docs/index.html`** and open it in any modern browser (Chrome, Edge, Safari, Firefox).

The file is about 730 KB, with all data, styles and scripts embedded: it needs no network, no server and no external libraries. You can copy it to a USB stick, send it to someone, or put it on your own website.

---

## 2. Online

https://jackyijun.github.io/zhanguo-map/

---

## 3. Build locally

You only need to rebuild after changing the historical content (`content/`) or the parameters (`src/config.py`). **Python 3.9 or later** is required.

**macOS / Linux**

```bash
cd zhanguo-map
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py --open
```

**Windows (PowerShell)**

```powershell
cd zhanguo-map
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py --open
```

A full build takes about 30 seconds and then opens the newly built `docs/index.html` in your browser.

| Command | What it does |
|---|---|
| `python run.py` | Download the base map if missing → compute territories → assemble the HTML |
| `python run.py --html` | Reassemble the HTML only (when you changed only `src/template.html`, text in `content/features.py`, or the English in `content/en/`; under a second) |
| `python run.py --draft` | Build even when English translations are missing or out of date (missing ones temporarily show the Chinese); for previews only. Without it the build stops and lists what is missing |
| `python run.py --open` | Open the result in a browser after building |
| `python run.py --preview -350,-260` | Also draw rough territory sketches for these nodes to `build/preview.png`, to check the ownership data |
| `python tools/preview.py -284 113,123,33,41` | Draw sketches only, optionally for a given extent (west,east,south,north) |

The base map data (`geodata/ne/`, about 23 MB) ships with the project, so it builds offline. If you delete it, `run.py` downloads the pinned version (Natural Earth v5.1.2) from GitHub.

The same input always produces a byte-for-byte identical build, so changes can be tracked with git.

When the build finishes, commit docs/index.html along with your changes and push to main; the online page updates automatically.

---

## 4. Directory layout

```
zhanguo-map/
├── run.py                 one-step build
├── requirements.txt
├── README.md · README.en.md   Chinese · English documentation
├── docs/
│   ├── index.html         ★ the finished map, a single file (GitHub Pages serves it)
│   └── .nojekyll          tells GitHub Pages to publish the files as they are
├── content/               ★ historical content (hand-written; this is what you edit)
│   ├── seeds.txt          386 ownership points: name, coordinates, which state held it when
│   ├── features.py        state profiles and colours, 37 time nodes and their timeline labels,
│   │                      capitals, battles, passes, major cities, towns, events and works,
│   │                      mountains, rivers, lakes and marshes, long walls, peoples,
│   │                      Qin commanderies, highways, and the falls of states for the chronology
│   └── en/                English translations
│       ├── items.json     entries (states, capitals, battles, places, mountains, rivers…)
│       ├── snaps.json     titles, timeline labels and summaries of the time nodes
│       ├── misc.json      modern province names, falls of states
│       ├── zh.lock.json   fingerprint of the Chinese each English string was based on
│       └── GLOSSARY.md    translation conventions
├── src/
│   ├── config.py          ★ all paths and tunable parameters (grid, costs, smoothing…)
│   ├── fetch_data.py      downloads the Natural Earth base map
│   ├── build.py           computes the territories, writes build/geo.json
│   ├── assemble.py        merges the English, checks for missing translations, injects
│   │                      the data into the template, writes docs/index.html
│   ├── i18n.py            shared English-version code: list of translatable fields, fingerprints
│   └── template.html      front end: page structure, styles, scripts (incl. both UI languages)
├── geodata/
│   ├── prov.json          modern provincial boundaries (simplified, encoded)
│   └── ne/                Natural Earth 1:10m GeoJSON (land, minor islands, rivers, lakes)
├── tools/
│   ├── preview.py         matplotlib territory sketches
│   └── i18n.py            English maintenance: status · todo · lock · table
└── build/                 intermediate files (safe to delete)
```

---

## 5. How it works

```
content/seeds.txt ──┐
content/features.py ┼─► build.py ─► build/geo.json ─► assemble.py ─► docs/index.html
geodata/ (base map) ┘                                    ▲
                          content/features.py + content/en/ + src/template.html
```

### 1. Why the territories are computed

There is no ready-made boundary data for the Warring States. What the sources usually tell us is that "in such a year, such a city belonged to such a state". So the approach is:

1. Write by hand only the **place → state** ownership and the years it changed (`seeds.txt`);
2. Let the computer infer the boundaries between states on a "travel cost" map, so that they tend to follow ridges and large rivers.

### 2. Steps in `build.py`

1. **Land**: clip East Asian land from Natural Earth, simplify and encode it.
2. **Cost grid**: one cell per 0.05°. Land costs 1, sea 4.5; every mountain range in `features.py` adds cost according to its "barrier weight", and the ancient Yellow River, the Ji, Yi and Beiluo rivers and the Yangtze, Han and Zhang also add cost; a layer of smooth noise with a fixed random seed then gives the boundaries a natural wobble.
3. **Multi-source shortest paths**: a Dijkstra search runs from all 386 ownership points at once, and each cell goes to the point that is "nearest to walk to". This is done only once.
4. **Colouring each node**: for every time node, look up which state each point belonged to that year (from `seeds.txt`), merge the cells into each state's area, smooth with a Gaussian, trace and simplify the outlines. Labels are placed at the point of each state's largest land area farthest from its edge.
5. **Qin commanderies**: for every node, take the commanderies already established whose seats lie inside Qin, run another multi-source shortest-path search from the seats on the same cost map, divide Qin's territory among them, and trace the commandery boundaries. These boundaries are therefore inferred by "nearest seat", not recorded in the sources.
6. **Rivers and lakes**: Natural Earth rivers are matched to ancient names by their English names; the Warring States course of the Yellow River, the Ji, Beiluo, Yi, Luo, Ru, Ying, Si, Hutuo and Yi rivers and others are drawn by hand. The modern lower Yellow River is drawn as a dashed line to show the change of course.
7. **Place ownership**: each city, pass and battle looks up whose cell it falls in and takes that point's ownership history, so the tooltip can say "held by such a state in such a year".

### 3. `seeds.txt` syntax

One point per line:

```
name longitude latitude initial-owner [year+owner ...]
```

- `·` means not held by any of the Zhou states (land of the Rong, Di, Man and Yi).
- Years BC are negative: `-330秦` means held by Qin from 330 BC.

Examples:

```
少梁 110.45 35.57 魏 -330秦
长平 112.92 35.8 韩 -262赵 -260秦 -257赵 -247秦
野王 112.93 35.09 韩 -262秦 -241卫 -209秦
会稽 120.58 30.0 越 -306· -222秦
```

After changing `seeds.txt`, or the time nodes, mountains or hand-drawn rivers in `features.py`, run the full `python run.py`. If you only changed text, `python run.py --html` is enough.

### 4. What is in `features.py`

| Name | Contents |
|---|---|
| `STATES` · `STATE_COLORS` | Clan names and profiles of the 17 states, and light / dark territory colours |
| `SNAPS` · `SNAP_SHORT` | 37 time nodes: year, title, a summary (the last is 212 BC, "The empire at its height"); the short labels set vertically on the timeline |
| `CAPITALS` | 37 capitals with start and end years (former capitals are shown as dashed squares) |
| `BATTLES` | 43 battles: year, outcome, commanders, course of events (including the Qin campaigns against the Hundred Yue and the Xiongnu after unification) |
| `PASSES` · `CITIES` · `TOWNS` | 20 passes and fords, 28 major cities, 145 towns |
| `CULTURE` | 27 events, reforms, schools, public works and archaeological sites (incl. the Lingqu Canal, Epang Palace, the burning of books) |
| `WALLS` · `WALL_END` · `RANGES` | 10 long walls (incl. the First Emperor's new sections), the interior walls abandoned after unification, 24 mountain ranges |
| `NE_RIVERS` · `MANUAL_RIVERS` · `CANALS` · `MARSHES` · `NE_LAKES` | Ancient river names, hand-drawn rivers, canals, ancient marshes, lakes |
| `PEOPLES` | 18 labels for neighbouring peoples, shown during the years they existed |
| `JUN` · `JUN_ALIAS` | 51 Qin commanderies (incl. Neishi): seat, modern location, year established, notes, and alternative names for searching (e.g. Linzi Commandery = Qi Commandery) |
| `ROADS` | Courses (schematic) and dates of the imperial highways, the Straight Road and the Five-Foot Road |
| `FALLS` | The falls of states for the chronology: year, state, what happened |

### 5. Display rules

- Battles are shown only for the **current period**, i.e. after the previous node (exclusive) up to this node (inclusive); the caption bar lists "Battles this period", and clicking one locates it. In the side list, this period's battles come first and the rest are greyed out; hovering shows them faintly on the map.
- Events and works, long walls and highways appear only once they have happened; capitals show only the current capitals and former ones.
- The interior long walls abandoned after the Qin unification (Wei, Zhao Southern, Yan Southern, Qi and Chu Fangcheng) are faded from the 212 BC node on and marked "(abandoned)".
- Qin commanderies are shown only once established and only when their seat is inside Qin: dashed boundaries, double-ring seat symbols. They can be switched off separately in the legend.
- Opening a battle from another period in the index, chronology or gazetteer jumps the timeline to its period; opening a "future" event jumps to the nearest node after it.
- Zoom levels: the full view shows only state names, capitals, battles and passes; major cities, towns and modern names appear as you zoom in.

---

## 6. Common changes

| To do this | Edit | Then run |
|---|---|---|
| Change who held a city in a given year | the matching line in `content/seeds.txt` (syntax above) | `python run.py` |
| Add a city, pass, battle or event | add a line to the matching list in `content/features.py`; to make it affect territories, also add an ownership point to `seeds.txt` | `features.py` only: `python run.py --html`; with `seeds.txt`: `python run.py` |
| Add a time node | add a line to `SNAPS` in `features.py` (year, title, summary) and a timeline label to `SNAP_SHORT` | `python run.py` |
| Change descriptive text | the notes and node summaries in `features.py` | `python run.py --html` (it will report the matching English as out of date; see the next section) |
| Change the English | `content/en/*.json` | `python tools/i18n.py lock` → `python run.py --html` |
| Change colours | `STATE_COLORS` in `features.py` (light and dark values) | `python run.py --html` |
| Change interface text | `U` in `src/template.html` (`zh` and `en` sets) | `python run.py --html` |

Once the Chinese is changed and the English updated, `python tools/i18n.py status` should show zero missing and zero out-of-date entries; only then does the strict build pass.

---

## 7. English version

One `docs/index.html` holds both a Chinese and an English interface, Chinese by default; switch with "中 | EN" at the top right of the map. The choice is remembered in the browser, and adding `#en` to the address opens the English directly. In English mode the map is labelled in English only, while tooltips, the index, the chronology and the gazetteer add the original Chinese in small type after each English name; search accepts both languages, and English search ignores case.

- **Chinese is the source text.** The English is stored separately in `content/en/` by "file · key · field": entry keys are `category:ancient name` (the second entry of the same category and name gets `#2`), node keys are years, modern provinces are `prov:name`, and falls of states are `fall:year`.
- **Fingerprints.** `zh.lock.json` records the first 10 hex digits of the sha1 of the Chinese each English string was based on. Once the Chinese changes, the English counts as out of date; `assemble.py` is strict by default and stops on missing or out-of-date translations, and only `--draft` lets them through.
- **Tools.** `python tools/i18n.py status` counts missing and out-of-date translations; `todo` exports the Chinese still to be translated to `build/i18n_todo.json`; `table` exports a Chinese–English table to `build/i18n_table.csv` (opens directly in Excel) for review; `lock` records fingerprints. The `names` / `notes` argument limits a command to names or to notes.
- **Translation conventions** are in `content/en/GLOSSARY.md`: pinyin, Wey for 卫, generic terms (Pass, Ford, Commandery, Long Wall…), modern locations, dates and more.

---

## 8. Tuning

All tunable parameters are in `src/config.py`:

| Parameter | Effect |
|---|---|
| `RES` | Grid cell size. Smaller is finer but slower |
| `SEA_COST` | Cost of crossing the sea. Raise it to stop territories joining across water |
| `NOISE_SEED` · `NOISE_AMP` | Random seed and amplitude of the boundary wobble |
| `RANGE_WIDTH` · `RIVER_COST` | Width of the ridge barrier band, cost of boundary rivers |
| `SMOOTH_SIGMA` · `POLY_SIMPLIFY` | Outline smoothing and simplification tolerance |

The barrier strength of each mountain range is set in `RANGES` in `features.py` (the 4th field).

---

## 9. Sources and reliability

- **Territories**: inferred from the *Shiji*, the *Zhanguo ce*, the *Bamboo Annals* and other sources, and from the general outline of the Warring States maps in volume 1 of Tan Qixiang's *Historical Atlas of China*; compiled with AI assistance and not checked line by line against the original texts. The overall picture and the key years (e.g. Wei ceding Hexi in 330 BC, the conquest of Ba and Shu in 316 BC, Yue Yi's crushing of Qi in 284 BC, Changping in 260 BC, Qin's conquest of the six states in 230–221 BC) are fairly reliable; the ownership of a particular city in a particular year, and the extent of the margins (Liaodong, Lingnan, the southwest), are rougher.
- **Boundaries**: entirely inferred, schematic lines. They only mean "this area belonged to this state", not that the sources record such a line.
- **Qin commanderies**: the *Shiji* says only that the realm was "divided into thirty-six commanderies" and gives no names. The list and seats mainly follow the 54-commandery reconstruction in Hou Xiaorong's *Qindai zhengqu dili* (2009), with reference to the treatise on geography in the *Hanshu*, the *Shuijing zhu*, Qin clay sealings and the Yuelu Academy and Liye Qin slips. Xinqinzhong, Jiaoxi, Hejian and Wuqian, whose seats are unknown, are not drawn; the seat of Cangwu is unknown and its position is a guess. Commanderies split off only after unification (Jibei, Jimo, Chengyang, Boyang, Donghai, Henei, Qinghe, Hengshan) are dated provisionally to 220 BC and appear only at the 212 BC node. Commandery boundaries are inferred from the seats, not recorded in the sources; coastal boundaries are clipped to the coastline.
- **Disputed points** are marked "one view" on the map, e.g. the locations of Maling, Yuyu, Zhongmou and Juyang; the fall of Yue follows Yang Kuan's c. 306 BC, against the traditional 334/333 BC.
- **English**: names and notes were translated by AI and independently reviewed; conventions are in `content/en/GLOSSARY.md`. Where the English and the Chinese disagree, the Chinese prevails.
- **Base map**: Natural Earth 1:10m (public domain); modern provincial boundaries are reused from the author's earlier map.

Corrections are welcome.
