# NOTICE

本项目代码使用 MIT。内置地铁数据来自 Open Metro 中国城市数据集及其上游来源，数据权利归各自所有者，不随 MIT 重新授权。

- Open Metro: https://github.com/Naptie/openmetro (MPL-2.0)
- 上海地铁官网: https://service.shmetro.com/
- 各城市地铁运营方官方公告/线路图/票价查询
- 百度地图公共交通路径规划（部分区间/换乘时间）
- OpenStreetMap / Wikidata（部分坐标与名称）

票价和首末班为开发时抓取/整理值，仅供离线出行参考；实际以运营方公告为准。

## 城市地铁标识

- 界面中的城市地铁标识来自 Wikimedia Commons（含公有领域、CC BY 3.0、CC BY-SA 3.0/4.0 等许可），内嵌后仅用于标识对应的地铁系统，不表示任何隶属或授权关系。
- 这些标识是各城市地铁运营方的注册商标，商标权归各运营方所有；本项目仅作指称性使用（nominative use）。若权利方要求，可随时移除。
- 目前 32 个城市/地区使用官方标识；大连、贵阳、昆明、兰州、武汉暂未在可自由使用的来源中找到官方标识文件，回退为「标志色 + 城市名」徽标。补图方式：把 PNG 放到 `assets/logos/<city-id>.png`，再运行 `python tools/embed_logos.py` 重新内嵌。

