"""英文版维护工具。

  python tools/i18n.py status               各类缺译、过期、未登记指纹的条数
  python tools/i18n.py todo [names|notes]   列出待译（缺译或过期）的中文，JSON 骨架输出到 build/i18n_todo.json
  python tools/i18n.py lock [names|notes]   为已有英文登记所据中文的指纹（改完中英文、核对无误后运行）
  python tools/i18n.py table [names|notes]  导出中英对照表 build/i18n_table.csv（Excel 可直接打开），供审校

names = 名称层（古名、今地、郡治、年代、胜负、主将、节点标题与短名、今省名、亡国名）
notes = 按语层（按语、节点概述、灭国经过）
"""
import csv, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
import config as C
import i18n
import assemble as A


def all_units():
    GEO, I = A.make()
    return i18n.units(I, GEO["snaps"], [p["n"] for p in GEO["prov"]], A.F.FALLS, A.F.SNAP_SHORT)


def layer(u, which):
    if not which: return True
    is_name = u[2] in i18n.NAME_FIELDS
    return is_name if which == "names" else not is_name


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    which = sys.argv[2] if len(sys.argv) > 2 else None
    us = [u for u in all_units() if layer(u, which)]
    en, lock = i18n.load()
    miss, stale, unreg = i18n.check(us, en, lock)

    if cmd == "status":
        for nm, w in (("名称", "names"), ("按语", "notes")):
            sub = [u for u in us if layer(u, w)]
            m, s, r = i18n.check(sub, en, lock)
            print(f"{nm}：共 {len(sub)} 条 · 缺译 {len(m)} · 过期 {len(s)} · 未登记指纹 {len(r)}")
        known = {(f, k, fld) for f, k, fld, _ in all_units()}
        orphan = [(f, k, fld) for f in i18n.FILES for k, v in en[f].items() for fld in v if (f, k, fld) not in known]
        if orphan:
            print(f"多余的英文（中文已删或改了键）{len(orphan)} 条，例如：", orphan[:5])
    elif cmd == "todo":
        out = {}
        for f, k, fld, zh in miss + stale:
            out.setdefault(f, {}).setdefault(k, {})[fld] = {"zh": zh, "en": en[f].get(k, {}).get(fld, "")}
        C.BUILD.mkdir(exist_ok=True)
        p = C.BUILD / "i18n_todo.json"
        p.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf8")
        print(f"待译 {len(miss)} 条、过期 {len(stale)} 条 → {p}")
    elif cmd == "lock":
        n = 0
        for f, k, fld, zh in us:
            if en[f].get(k, {}).get(fld):
                lock[i18n.lid(f, k, fld)] = i18n.fp(zh); n += 1
        i18n.save(lock=lock)
        print(f"已登记 {n} 条指纹")
    elif cmd == "table":
        C.BUILD.mkdir(exist_ok=True)
        p = C.BUILD / "i18n_table.csv"
        with open(p, "w", encoding="utf-8-sig", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["文件", "键", "字段", "中文", "English", "状态"])
            bad = {(f, k, fld): s for s, lst in (("缺译", miss), ("过期", stale), ("未登记", unreg)) for f, k, fld, _ in lst}
            for f, k, fld, zh in us:
                w.writerow([f, k, fld, zh, en[f].get(k, {}).get(fld, ""), bad.get((f, k, fld), "")])
        print(f"对照表 {len(us)} 行 → {p}")
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
