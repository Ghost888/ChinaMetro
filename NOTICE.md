# NOTICE

本项目代码使用 MIT。内置地铁数据来自 Open Metro 中国城市数据集及其上游来源，数据权利归各自所有者，不随 MIT 重新授权。

- Open Metro: https://github.com/Naptie/openmetro (MPL-2.0)
- 上海地铁官网: https://service.shmetro.com/
- 各城市地铁运营方官方公告/线路图/票价查询
- 百度地图公共交通路径规划（部分区间/换乘时间）
- OpenStreetMap / Wikidata（部分坐标与名称）

票价和首末班为开发时抓取/整理值，仅供离线出行参考；实际以运营方公告为准。

## 城市地铁标识

- 界面中的城市地铁标识来自 Wikimedia Commons 与中英文维基百科（含公有领域、CC BY 3.0、CC BY-SA 3.0/4.0，以及英文维基的 fair use 文件），内嵌后仅用于标识对应的地铁系统，不表示任何隶属或授权关系。
- 这些标识是各城市地铁运营方的注册商标，商标权归各运营方所有；本项目仅作指称性使用（nominative use）。若权利方要求，可随时移除。
- 目前 37 个城市/地区均使用官方标识（逐条来源见 `assets/logos/index.json`）。补图或替换：把 PNG 放到 `assets/logos/<city-id>.png`，在 `index.json` 补一条来源，再运行 `python tools/embed_logos.py` 重新内嵌。

