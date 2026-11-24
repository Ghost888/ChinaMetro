#!/usr/bin/env python3
"""把 assets/logos/ 下的城市地铁标识内嵌进 app_template.html。

背景：`ChinaMetro.html` 是单文件交付，标识必须内联成 data URI，不能外链。
本脚本把 PNG 缩到 96×96 并转成 base64，写进模板里的 `const CITY_LOGOS={...};` 常量。

用法：
    python tools/embed_logos.py                 # 重新内嵌 assets/logos/ 下所有标识
    python tools/embed_logos.py --size 128      # 改内嵌分辨率
    python tools/build.py                       # 再构建 ChinaMetro.html

补图：把官方标识存成 `assets/logos/<city-id>.png`（如 `cn-wuhan.png`），
在 index.json 里补一条来源信息，然后重跑本脚本即可。

注意：这些标识是各运营方的注册商标，仅作指称性使用；许可与来源见 NOTICE.md。
"""
import argparse, base64, io, json, os, re, sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO_DIR = os.path.join(ROOT, "assets", "logos")
TPL = os.path.join(ROOT, "app_template.html")
HEADER = "/* 城市地铁官方标识（来源：Wikimedia Commons，仅用于识别各城市地铁系统） */\n"


def build_block(size):
    index = json.load(open(os.path.join(LOGO_DIR, "index.json"), encoding="utf-8"))
    entries, total = [], 0
    for cid in sorted(index):
        p = os.path.join(LOGO_DIR, cid + ".png")
        if not os.path.exists(p):
            print("skip (missing png):", cid, file=sys.stderr)
            continue
        im = Image.open(p).convert("RGBA").resize((size, size), Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, "PNG", optimize=True)
        raw = buf.getvalue()
        total += len(raw)
        entries.append('"%s":"data:image/png;base64,%s"' % (cid, base64.b64encode(raw).decode("ascii")))
    block = HEADER + "const CITY_LOGOS={%s};\n" % ",".join(entries)
    return block, len(entries), total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", type=int, default=96, help="内嵌 PNG 边长，默认 96")
    args = ap.parse_args()

    block, n, total = build_block(args.size)
    tpl = open(TPL, encoding="utf-8").read()
    pattern = re.compile(r"/\* 城市地铁官方标识[^\n]*\nconst CITY_LOGOS=\{.*?\};\n", re.S)
    if pattern.search(tpl):
        tpl = pattern.sub(lambda m: block, tpl)
    else:
        tpl = tpl.replace("const APP_VERSION = ", block + "const APP_VERSION = ", 1)
    open(TPL, "w", encoding="utf-8").write(tpl)
    print("embedded %d logos, %.0f KB raw, %.0f KB base64" % (n, total / 1024, total * 4 / 3 / 1024))
    print("now run: python tools/build.py")


if __name__ == "__main__":
    main()
