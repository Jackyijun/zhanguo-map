"""下载 Natural Earth 底图（仓库里已经带了，缺失时才需要）。"""
import urllib.request
import config as C

URL = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/{tag}/geojson/{name}.geojson"

def ensure():
    C.NE.mkdir(parents=True, exist_ok=True)
    for name in C.NE_FILES:
        f = C.NE / f"{name}.geojson"
        if f.exists(): continue
        url = URL.format(tag=C.NE_TAG, name=name)
        print("下载", url)
        urllib.request.urlretrieve(url, f)

if __name__ == "__main__":
    ensure()
