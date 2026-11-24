#!/usr/bin/env python3
"""把所有城市的 OSM 底图按城市尺寸重新抓取到尽可能高的 zoom（受单城面积预算约束）。

为什么要升级：原底图统一用 z10，澳门这种小城市只占底图宽度的 6%，放大后就是一片糊；
大城市在 z10 只有 ~700 px/°，放大 2 倍就明显发虚。这里按城市 bbox 选尽可能高的 zoom，
同时给每城一个面积上限（默认 4 MP ≈ 600~800 KB JPEG），控制单文件总体积。

用法：
    python tools/upgrade_tiles.py                      # 全部城市，面积上限 4 MP
    python tools/upgrade_tiles.py --city cn-shanghai   # 只处理指定城市
    python tools/upgrade_tiles.py --max-mp 5 --max-kb 900
    python tools/upgrade_tiles.py --dry-run

瓦片来源 tile.openstreetmap.de（OSM 主站对批量请求返回 403）。按 OSM 瓦片使用政策限速，
已有瓦片会命中本地缓存，中断后重跑不会重复下载。
"""
import argparse, base64, io, json, math, os, sys, time, urllib.error, urllib.request

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TILE_URLS = [
    "https://tile.openstreetmap.de/{z}/{x}/{y}.png",
    "https://a.tile.openstreetmap.fr/osmfr/{z}/{x}/{y}.png",
]
UA = "ChinaMetro-offline/1.0 (+https://github.com/Ghost888/ChinaMetro)"
MARGIN = 0.008


def merc(lon, lat):
    return (lon + 180) / 360, (1 - math.log(math.tan(math.pi / 4 + lat * math.pi / 360)) / math.pi) / 2


def fetch(tile_url, tries=4):
    """按镜像顺序取瓦片；osm.de 在部分区域/层级会 404，回退到 osm.fr 镜像。"""
    last = None
    for tpl in TILE_URLS:
        url = tpl.format(**tile_url)
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "image/png,image/*"})
        for i in range(tries):
            try:
                body = urllib.request.urlopen(req, timeout=40).read()
                if not is_tile_png(body):
                    raise ValueError("bad tile body (%d bytes)" % len(body))
                return body
            except urllib.error.HTTPError as e:
                last = e
                if e.code == 404:      # 该镜像没有这张瓦片，换镜像
                    break
                time.sleep(4 * (i + 1))
            except Exception as e:      # noqa: BLE001
                last = e
                time.sleep(4 * (i + 1))
    raise RuntimeError("tile failed %s: %s" % (tile_url, last))


def is_tile_png(body):
    """OSM 空白瓦片可能只有几百字节，因此按 PNG 头 + 256x256 尺寸校验，而不是按体积。"""
    if body[:8] != b"\x89PNG\r\n\x1a\n" or len(body) < 33:
        return False
    w = int.from_bytes(body[16:20], "big")
    h = int.from_bytes(body[20:24], "big")
    return w == 256 and h == 256


def choose_zoom(st, max_mp):
    lons = [s[2] for s in st]
    lats = [s[3] for s in st]
    lon0, lon1 = min(lons) - MARGIN, max(lons) + MARGIN
    lat0, lat1 = min(lats) - MARGIN, max(lats) + MARGIN
    best = None
    for z in range(10, 18):
        n = 2 ** z
        tx0 = math.floor(merc(lon0, 0)[0] * n)
        tx1 = math.floor(merc(lon1, 0)[0] * n)
        ty0 = math.floor(merc(0, lat1)[1] * n)
        ty1 = math.floor(merc(0, lat0)[1] * n)
        cw, ch = tx1 - tx0 + 1, ty1 - ty0 + 1
        mp = cw * ch * 65536 / 1e6
        if mp <= max_mp:
            best = (z, tx0, ty0, cw, ch, mp)
        else:
            break
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=os.path.join(ROOT, "china_db.json"))
    ap.add_argument("--cache", default=os.path.join(ROOT, ".tile-cache"))
    ap.add_argument("--max-mp", type=float, default=4.0, help="单城底图像素上限（百万像素）")
    ap.add_argument("--max-kb", type=int, default=800, help="单城 JPEG 上限")
    ap.add_argument("--quality", type=int, default=62)
    ap.add_argument("--city", nargs="*", default=None)
    ap.add_argument("--sleep", type=float, default=0.8)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    db = json.load(open(args.db, encoding="utf-8"))
    os.makedirs(args.cache, exist_ok=True)
    todo = [c for c in db["cities"] if not args.city or c["id"] in args.city]
    total_tiles = 0
    for idx, c in enumerate(todo, 1):
        plan = choose_zoom(c["stations"], args.max_mp)
        if not plan:
            print("skip", c["id"], "no zoom fits")
            continue
        z, tx0, ty0, cw, ch, mp = plan
        print("[%d/%d] %-16s %-6s z%-2d %dx%-2d %4.1f MP" % (idx, len(todo), c["id"], c.get("name", ""), z, cw, ch, mp), flush=True)
        if args.dry_run:
            total_tiles += cw * ch
            continue
        img = Image.new("RGB", (cw * 256, ch * 256))
        for x in range(tx0, tx0 + cw):
            for y in range(ty0, ty0 + ch):
                p = os.path.join(args.cache, "z%d_%d_%d.png" % (z, x, y))
                if not (os.path.exists(p) and os.path.getsize(p) > 100):
                    open(p, "wb").write(fetch({"z": z, "x": x, "y": y}))
                    time.sleep(args.sleep)
                img.paste(Image.open(p).convert("RGB"), ((x - tx0) * 256, (y - ty0) * 256))
                total_tiles += 1
        q = args.quality
        while True:
            buf = io.BytesIO()
            img.save(buf, "JPEG", quality=q, optimize=True, progressive=False)
            if len(buf.getvalue()) <= args.max_kb * 1024 or q <= 45:
                break
            q -= 5
        jpg = buf.getvalue()
        c["tileMosaic"] = [z, tx0, ty0, img.width, img.height, base64.b64encode(jpg).decode("ascii")]
        c["tileZ"] = z
        c["tileMime"] = "image/jpeg"
        c["tileSource"] = "OpenStreetMap"
        c.pop("tiles", None)
        print("        %dx%d q%d %.0f KB" % (img.width, img.height, q, len(jpg) / 1024), flush=True)
        json.dump(db, open(args.db, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

    if args.dry_run:
        print("DRY RUN: %d cities, %d tiles" % (len(todo), total_tiles))
        return
    size = os.path.getsize(args.db)
    payload = sum(len(c["tileMosaic"][5]) for c in db["cities"] if c.get("tileMosaic"))
    print("\ntiles fetched/used: %d" % total_tiles)
    print("db %.1f MB, tile base64 payload %.1f MB" % (size / 1e6, payload / 1e6))
    print("now run: python tools/build.py")


if __name__ == "__main__":
    main()
