#!/usr/bin/env python3
"""把数据库里的车站坐标从 GCJ-02（火星坐标）转成 WGS-84，使其与 OSM 底图对齐。

背景：Open Metro 的中国城市车站坐标来自国内地图源，是 GCJ-02 加密坐标；OSM 瓦片是
WGS-84。两者在城市尺度上差约 300~700 m —— z10 底图下只有 3~4 px 看不出来，底图换成
z15 后就是一眼可见的错位（澳门约 118 px）。

实测（与 OSM 铁路站点节点比对最近距离的中位数）：
  上海 534 m -> 137 m，北京 638 m -> 33 m，乌鲁木齐 327 m -> 48 m
  香港 606 m -> 155 m（用 463 个铁路/电车站节点拟合最佳平移，得到 dx=-0.0055, dy=+0.0025，
  与 GCJ 在该处的偏移 (-0.0050, +0.0029) 几乎一致）
  澳门：视觉核对，转换后「蓮花」正好落在 OSM 的 Lotus 站符号上

用法（构建 DB 之后、build.py 之前）：
    python tools/fix_coord_datum.py                 # 处理 china_db.json 与 china_db_base.json
    python tools/fix_coord_datum.py --db china_db.json
    python tools/fix_coord_datum.py --dry-run

已转换的城市会写入 coordDatum="WGS84"，重复运行会跳过，不会二次偏移。
"""
import argparse, json, math, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = 6378245.0
EE = 0.00669342162296594323
# 需要排除的城市（目前没有）
SKIP = set()


def out_of_china(lon, lat):
    return not (72.004 <= lon <= 137.8347 and 0.8293 <= lat <= 55.8271)


def transform_lat(x, y):
    r = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y + 0.2 * math.sqrt(abs(x))
    r += (20.0 * math.sin(6.0 * x * math.pi) + 20.0 * math.sin(2.0 * x * math.pi)) * 2.0 / 3.0
    r += (20.0 * math.sin(y * math.pi) + 40.0 * math.sin(y / 3.0 * math.pi)) * 2.0 / 3.0
    r += (160.0 * math.sin(y / 12.0 * math.pi) + 320 * math.sin(y * math.pi / 30.0)) * 2.0 / 3.0
    return r


def transform_lon(x, y):
    r = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * math.sqrt(abs(x))
    r += (20.0 * math.sin(6.0 * x * math.pi) + 20.0 * math.sin(2.0 * x * math.pi)) * 2.0 / 3.0
    r += (20.0 * math.sin(x * math.pi) + 40.0 * math.sin(x / 3.0 * math.pi)) * 2.0 / 3.0
    r += (150.0 * math.sin(x / 12.0 * math.pi) + 300.0 * math.sin(x / 30.0 * math.pi)) * 2.0 / 3.0
    return r


def gcj_to_wgs(lon, lat):
    if out_of_china(lon, lat):
        return lon, lat
    dlat = transform_lat(lon - 105.0, lat - 35.0)
    dlon = transform_lon(lon - 105.0, lat - 35.0)
    radlat = lat / 180.0 * math.pi
    magic = 1 - EE * math.sin(radlat) ** 2
    sqrtmagic = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((A * (1 - EE)) / (magic * sqrtmagic) * math.pi)
    dlon = (dlon * 180.0) / (A / sqrtmagic * math.cos(radlat) * math.pi)
    return lon - dlon, lat - dlat


def fix_db(path, dry_run=False):
    db = json.load(open(path, encoding="utf-8"))
    changed = []
    for c in db["cities"]:
        if c["id"] in SKIP or c.get("coordDatum") == "WGS84":
            continue
        n = 0
        for s in c["stations"]:
            lon, lat = gcj_to_wgs(s[2], s[3])
            if abs(lon - s[2]) > 1e-12 or abs(lat - s[3]) > 1e-12:
                n += 1
            s[2], s[3] = round(lon, 6), round(lat, 6)
        c["coordDatum"] = "WGS84"
        changed.append((c["id"], n))
    if not dry_run:
        json.dump(db, open(path, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print("%s: %d cities converted%s" % (os.path.basename(path), len(changed), " (dry-run)" if dry_run else ""))
    for cid, n in changed[:5]:
        print("   ", cid, n, "stations")
    if len(changed) > 5:
        print("    ...")
    return changed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", nargs="*", default=None)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    paths = args.db or [os.path.join(ROOT, "china_db.json"), os.path.join(ROOT, "china_db_base.json")]
    for p in paths:
        if not os.path.exists(p):
            print("skip (missing):", p, file=sys.stderr)
            continue
        fix_db(p, args.dry_run)
    print("done; now run: python tools/build.py")


if __name__ == "__main__":
    main()
