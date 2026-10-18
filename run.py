"""一键构建：python run.py  →  docs/index.html

  python run.py              底图缺失则下载 → 计算疆域 → 拼装 HTML
  python run.py --html       只重新拼装 HTML（只改了 src/template.html 或 content/features.py 里的文字时用）
  python run.py --open       构建完后在浏览器中打开
  python run.py --preview -350,-260   额外画出这几个节点的疆域草图到 build/preview.png
"""
import argparse, subprocess, sys, time, webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"

def step(name, script, *args):
    t = time.time()
    print(f"── {name}")
    r = subprocess.run([sys.executable, str(SRC / script), *args], cwd=ROOT)
    if r.returncode:
        sys.exit(f"失败：{script}")
    print(f"   完成（{time.time() - t:.1f}s）")

def main():
    ap = argparse.ArgumentParser(description="构建战国列国形势图")
    ap.add_argument("--html", action="store_true", help="只重新拼装 HTML")
    ap.add_argument("--open", action="store_true", help="构建后在浏览器打开")
    ap.add_argument("--preview", metavar="YEARS", help="画疆域草图，如 -350,-260")
    a = ap.parse_args()
    if not a.html:
        step("检查底图", "fetch_data.py")
        step("计算疆域", "build.py")
    elif not (ROOT / "build" / "geo.json").exists():
        sys.exit("build/geo.json 不存在，请先完整运行一次 python run.py")
    step("拼装 HTML", "assemble.py")
    out = ROOT / "docs" / "index.html"
    print(f"完成：{out}（{out.stat().st_size // 1024} KB）")
    if a.preview:
        subprocess.run([sys.executable, str(ROOT / "tools" / "preview.py"), a.preview], cwd=ROOT)
    if a.open:
        webbrowser.open(out.as_uri())

if __name__ == "__main__":
    main()
