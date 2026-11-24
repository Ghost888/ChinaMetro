#!/usr/bin/env python3
"""为单个城市重新抓取 OSM 瓦片并拼成一张底图，写回 china_db.json。

背景：底图按城市 bbox 拼成单张图。若城市面积远小于所取 zoom 的一张瓦片覆盖范围，
城市只占底图很小一块，显示时被放大，就会「很糊」。澳门 z10 时城市宽度只占底图 6%，
因此需要按城市单独取更高的 zoom（澳门用 z15）。

用法：
  python tools/attach_city_tiles.py --city cn-macau --zoom 15
  python tools/attach_city_tiles.py --city cn-urumqi --zoom 13 --max-kb 420
  python tools/attach_city_tiles.py --city cn-taiyuan cn-shijiazhuang --zoom 13

抓完记得重新构建：python tools/build.py
瓦片来源为 OSM 德国镜像 tile.openstreetmap.de（主站对批量请求返回 403）。
请遵守 OSM 瓦片使用政策：本脚本按 ~1.2 请求/秒 限速，只补个别城市。
"""
import argparse, base64, io, json, math, os, sys, time, urllib.request

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TILE_URL = "https://tile.openstreetmap.de/{z}/{x}/{y}.png"
UA = "ChinaMetro-offline/1.0 (+https://github.com/Ghost888/ChinaMetro)"


def merc(lon, lat):
    return (lon + 180) / 360, (1 - math.log(math.tan(math.pi / 4 + lat * math.pi / 360)) / math.pi) / 2


def tile_xy(lon, lat, z):
    n = 2 ** z
    x, y = merc(lon, lat)
    return x * n, y * n


def fetch(url, tries=5):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "image/png,image/*"})
    last = None
    for i in range(tries):
        try:
            body = urllib.request.urlopen(req, timeout=30).read()
            if body[:8] != b"\x89PNG\r\n\x1a\n" or len(body) < 1500:
                raise ValueError("suspicious tile body (%d bytes)" % len(body))
            return body
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(4 * (i + 1))
    raise RuntimeError("failed %s: %s" % (url, last))


def build_mosaic(tx0, ty0, tx1, ty1, z, cache_dir):
    os.makedirs(cache_dir, exist_ok=True)
    img = Image.new("RGB", ((tx1 - tx0 + 1) * 256, (ty1 - ty0 + 1) * 256))
    count = 0
    for x in range(tx0, tx1 + 1):
        for y in range(ty0, ty1 + 1):
            p = os.path.join(cache_dir, "%d_%d.png" % (x, y))
            if not (os.path.exists(p) and os.path.getsize(p) > 1500):
                open(p, "wb").write(fetch(TILE_URL.format(z=z, x=x, y=y)))
                time.sleep(0.80)  # ~1.2 req/s，遵守 OSM 瓦片政策
            img.paste(Image.open(p).convert("RGB"), ((x - tx0) * 256, (y - ty0) * 256))
            count += 1
    return img, count


def encode(img, max_kb):
    best = None
    for q in (80, 75, 70, 65, 60, 55):
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=q, optimize=True)
        data = buf.getvalue()
        if best is None:
            best = data
        if len(data) <= max_kb * 1024:
            return data, q
        best = data
    return best, 55


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--city", nargs="+", required=True, help="城市 id，如 cn-macau")
    ap.add_argument("--zoom", type=int, required=True, help="瓦片 zoom，如 15")
    ap.add_argument("--margin", type=float, default=0.006, help="bbox 外扩角度，默认 0.006°")
    ap.add_argument("--max-kb", type=int, default=450, help="单张底图 JPEG 上限，默认 450 KB")
    ap.add_argument("--db", default=os.path.join(ROOT, "china_db.json"))
    ap.add_argument("--cache", default=os.path.join(ROOT, ".tile-cache"))
    args = ap.parse_args()

    db = json.load(open(args.db, encoding="utf-8"))
    by_id = {c["id"]: c for c in db["cities"]}
    for cid in args.city:
        c = by_id.get(cid)
        if not c:
            sys.exit("unknown city: %s" % cid)
        st = c["stations"]
        lons = [s[2] for s in st]
        lats = [s[3] for s in st]
        x0f, y1f = tile_xy(min(lons) - args.margin, min(lats) - args.margin, args.zoom)
        x1f, y0f = tile_xy(max(lons) + args.margin, max(lats) + args.margin, args.zoom)
        tx0, tx1 = int(math.floor(x0f)), int(math.floor(x1f))
        ty0, ty1 = int(math.floor(y0f)), int(math.floor(y1f))
        span_deg = (tx1 - tx0 + 1) * 360 / (2 ** args.zoom)
        city_deg = max(lons) - min(lons)
        img, n = build_mosaic(tx0, ty0, tx1, ty1, args.zoom, args.cache)
        jpg, q = encode(img, args.max_kb)
        c["tileMosaic"] = [args.zoom, tx0, ty0, img.width, img.height, base64.b64encode(jpg).decode("ascii")]
        c["tileZ"] = args.zoom
        c["tileMime"] = "image/jpeg"
        c["tileSource"] = "OpenStreetMap"
        c.pop("tiles", None)
        print("%s %s: z%d %dx%d px, %d tiles, q%d, %.0f KB, city/mosaic=%.2f"
              % (cid, c.get("name", ""), args.zoom, img.width, img.height, n, q,
                 len(jpg) / 1024, city_deg / span_deg), flush=True)

    json.dump(db, open(args.db, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print("wrote", args.db, os.path.getsize(args.db), "bytes; now run: python tools/build.py")


if __name__ == "__main__":
    main()
