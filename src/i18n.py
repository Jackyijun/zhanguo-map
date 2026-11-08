"""英文版的公共部分：列出全部需要翻译的中文字段，读写 content/en/ 下的译文与指纹。

中文是源文本。每条英文都按“文件 · 键 · 字段”对应一条中文，并在 content/en/zh.lock.json
里记下所据中文的指纹（sha1 前 10 位）。中文一改，指纹对不上，这条英文就算“过期”。
"""
import hashlib, json
import config as C

EN = C.CONTENT / "en"
LOCK = EN / "zh.lock.json"
FILES = ("items", "snaps", "misc")

# 条目里要翻译的字段；名称层先译、交用户审定，按语层后译
ITEM_FIELDS = ("old", "mod", "zhi", "yt", "sides", "cmd", "note")
NAME_FIELDS = {"old", "mod", "zhi", "yt", "sides", "cmd", "t", "s", "nm", "n"}


def fp(s):
    return hashlib.sha1(s.encode("utf8")).hexdigest()[:10]


def item_keys(items):
    """条目键：类别:古名；同类同名的第二条起加 #2、#3。"""
    seen, keys = {}, []
    for it in items:
        k = f'{it["c"]}:{it["old"]}'
        seen[k] = seen.get(k, 0) + 1
        keys.append(k if seen[k] == 1 else f"{k}#{seen[k]}")
    return keys


def units(items, snaps, prov, falls, short):
    """全部待译单元：(文件, 键, 字段, 中文)。空字段不算。"""
    out = []
    for k, it in zip(item_keys(items), items):
        for f in ITEM_FIELDS:
            v = it.get(f)
            if isinstance(v, str) and v.strip() and v != "—":
                out.append(("items", k, f, v))
    for s in snaps:
        y = str(s["y"])
        out.append(("snaps", y, "t", s["t"]))
        out.append(("snaps", y, "s", short[s["y"]]))
        out.append(("snaps", y, "d", s["d"]))
    for p in prov:
        out.append(("misc", "prov:" + p, "n", p))
    seen = set()
    for s in snaps:                      # 当年别名
        for k, nm in s.get("lab", {}).items():
            if (k, nm) in seen: continue
            seen.add((k, nm)); out.append(("misc", f"alias:{k}:{nm}", "n", nm))
    for y, nm, p, _ in falls:
        out.append(("misc", f"fall:{y}", "nm", nm))
        out.append(("misc", f"fall:{y}", "p", p))
    return out


def load():
    en = {f: (json.load(open(EN / f"{f}.json", encoding="utf8")) if (EN / f"{f}.json").exists() else {}) for f in FILES}
    lock = json.load(open(LOCK, encoding="utf8")) if LOCK.exists() else {}
    return en, lock


def save(en=None, lock=None):
    EN.mkdir(exist_ok=True)
    dump = lambda o, p: open(p, "w", encoding="utf8").write(json.dumps(o, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    if en is not None:
        for f in FILES:
            dump(en[f], EN / f"{f}.json")
    if lock is not None:
        dump(lock, LOCK)


def lid(f, k, fld):
    return f"{f}|{k}|{fld}"


def check(us, en, lock):
    """返回 (缺译, 过期, 未登记) 三个列表，元素为 (文件, 键, 字段, 中文)。"""
    miss, stale, unreg = [], [], []
    for f, k, fld, zh in us:
        e = en[f].get(k, {}).get(fld)
        if not e:
            miss.append((f, k, fld, zh))
        elif lid(f, k, fld) not in lock:
            unreg.append((f, k, fld, zh))
        elif lock[lid(f, k, fld)] != fp(zh):
            stale.append((f, k, fld, zh))
    return miss, stale, unreg
