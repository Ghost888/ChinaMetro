# Test Report · China Metro Offline

**测试日期：** 2026-11-23  
**版本：** 1.0.0  
**数据版本：** 2026.11.23

## 1. 结论

- 自动化功能测试：**34/34 通过**
- 模块显示测试：**17/17 通过**（14 张截图，见 `DISPLAY_TESTS.md`）
- 页面错误：**0**
- 外部网络请求：**0**（离线上下文 + `file://`）
- 数据库结构校验：**0 errors / 0 warnings**
- WebKit（Safari 内核）检查：**通过**
- 桌面 iframe 嵌入：**通过**

## 2. 测试环境

| 项目 | 值 |
|---|---|
| 操作系统 | macOS（Apple Silicon） |
| Chromium | Chrome for Testing / Headless Shell 151 |
| WebKit | Playwright WebKit 2388（Safari 内核） |
| 页面协议 | `file://` |
| 网络 | `browser.newContext({ offline: true })` |
| 视口 | 1280×900 桌面；390×844 手机 |

## 3. 功能测试明细

| # | 用例 | 结果 | 备注 |
|---:|---|---|---|
| 1 | 初始化无异常 | ✅ 通过 | [] |
| 2 | 上海默认城市 | ✅ 通过 | {"cities": 37, "city": "上海", "stations": 417, "lines": 20, "title": "中国地铁 · 离线导航", "size": 16019455} |
| 3 | 城市数量 37 | ✅ 通过 |  |
| 4 | 37 城均有 OSM 底图 | ✅ 通过 | [] |
| 5 | 页面标题 | ✅ 通过 |  |
| 6 | 城市选择列表 | ✅ 通过 |  |
| 7 | 切换北京 | ✅ 通过 | {"city": "北京", "lines": 28, "stations": 423} |
| 8 | 上海 莘庄→迪士尼 路线 | ✅ 通过 | {"city": "上海", "route": true, "fare": 6, "ok": true, "total": 69, "transfers": 1, "sameLine": 0, "legs": ["1号线… |
| 9 | 上海 票价=6 | ✅ 通过 |  |
| 10 | 上海 时间合理 | ✅ 通过 |  |
| 11 | 11号线支线换向 | ✅ 通过 | {"city": "上海", "route": true, "fare": 5, "ok": true, "total": 43, "transfers": 0, "sameLine": 1, "legs": ["11号… |
| 12 | 5号线支线换向 | ✅ 通过 | {"city": "上海", "route": true, "fare": 5, "ok": true, "total": 45, "transfers": 0, "sameLine": 1, "legs": ["5号线… |
| 13 | 10号线支线换向 | ✅ 通过 | {"city": "上海", "route": true, "fare": 4, "ok": true, "total": 24, "transfers": 0, "sameLine": 1, "legs": ["10号… |
| 14 | 4号线环线 | ✅ 通过 | {"city": "上海", "route": true, "fare": 3, "ok": true, "total": 5, "transfers": 0, "sameLine": 0, "legs": ["4号线"… |
| 15 | 11号线直通服务不误拆 | ✅ 通过 | {"city": "上海", "route": true, "fare": 10, "ok": true, "total": 99, "transfers": 0, "sameLine": 0, "legs": ["11… |
| 16 | 5号线直通服务不误拆 | ✅ 通过 | {"city": "上海", "route": true, "fare": 5, "ok": true, "total": 28, "transfers": 0, "sameLine": 0, "legs": ["5号线… |
| 17 | 10号线直通服务不误拆 | ✅ 通过 | {"city": "上海", "route": true, "fare": 7, "ok": true, "total": 60, "transfers": 0, "sameLine": 0, "legs": ["10号… |
| 18 | 北京跨线路线 | ✅ 通过 | {"city": "北京", "route": true, "fare": 4, "ok": true, "total": 30, "transfers": 1, "sameLine": 0, "legs": ["2号线… |
| 19 | 广州路线 | ✅ 通过 | {"city": "广州", "route": true, "fare": 6, "ok": true, "total": 45, "transfers": 2, "sameLine": 0, "legs": ["三号线… |
| 20 | 深圳路线 | ✅ 通过 | {"city": "深圳", "route": true, "fare": 4, "ok": true, "total": 37, "transfers": 1, "sameLine": 0, "legs": ["3号线… |
| 21 | 成都路线 | ✅ 通过 | {"city": "成都", "route": true, "fare": 2, "ok": true, "total": 5, "transfers": 0, "sameLine": 0, "legs": ["2号线"… |
| 22 | 武汉路线 | ✅ 通过 | {"city": "武汉", "route": true, "fare": 6, "ok": true, "total": 48, "transfers": 0, "sameLine": 0, "legs": ["2号线… |
| 23 | 西安路线 | ✅ 通过 | {"city": "西安", "route": true, "fare": 2, "ok": true, "total": 14, "transfers": 0, "sameLine": 0, "legs": ["地铁2… |
| 24 | 37 城市均可计算路线 | ✅ 通过 | [] |
| 25 | 末班车拦截 | ✅ 通过 | {"city": "上海", "route": true, "fare": 6, "ok": false, "total": null, "transfers": 1, "sameLine": 0, "legs": ["… |
| 26 | 首班车前等待 | ✅ 通过 | {"city": "上海", "route": true, "fare": 6, "ok": true, "total": 172, "transfers": 1, "sameLine": 0, "legs": ["1号… |
| 27 | 同站提示 | ✅ 通过 |  |
| 28 | 车站搜索 | ✅ 通过 |  |
| 29 | 车站选择生效 | ✅ 通过 |  |
| 30 | 数据说明可见 | ✅ 通过 |  |
| 31 | 移动端无异常 | ✅ 通过 | [] |
| 32 | 路线计算性能 <100ms | ✅ 通过 |  |
| 33 | 无网络请求 | ✅ 通过 | [] |
| 34 | 无页面错误 | ✅ 通过 | [] |

## 4. 显示测试明细

| # | 场景 | 结果 | 截图 |
|---:|---|---|---|
| 1 | 首页初始化 | ✅ 通过 | `display/` |
| 2 | 上海 OSM 底图 | ✅ 通过 | `display/` |
| 3 | 城市列表 37 | ✅ 通过 | `display/` |
| 4 | 站点搜索 | ✅ 通过 | `display/` |
| 5 | 上海路线与票价 | ✅ 通过 | `display/` |
| 6 | 支线同站换向显示 | ✅ 通过 | `display/` |
| 7 | 末班车警告显示 | ✅ 通过 | `display/` |
| 8 | 北京路线与 OSM 底图 | ✅ 通过 | `display/` |
| 9 | 数据说明 | ✅ 通过 | `display/` |
| 10 | 底图开关 | ✅ 通过 | `display/` |
| 11 | 运营时间外徽章有文字 | ✅ 通过 | `display/` |
| 12 | 时间选择器可打开 | ✅ 通过 | `display/` |
| 13 | 点击选择时间生效 | ✅ 通过 | `display/` |
| 14 | 非上海深度缩放不露白 | ✅ 通过 | `display/` |
| 15 | 少许放大拖动线路可见 | ✅ 通过 | `display/` |
| 16 | 移动端无错误 | ✅ 通过 | `display/` |
| 17 | 页面无错误 | ✅ 通过 | `display/` |

## 5. 覆盖城市

| 城市 | 线路 | 车站 | 票价覆盖 |
|---|---:|---:|---:|
| 北京 | 28 | 423 | 100% |
| 长春 | 8 | 142 | 100% |
| 长沙 | 7 | 143 | 96% |
| 成都 | 18 | 389 | 100% |
| 重庆 | 13 | 271 | 98% |
| 大连 | 6 | 100 | 100% |
| 福州 | 6 | 101 | 100% |
| 广州 | 31 | 503 | 94% |
| 贵阳 | 4 | 93 | 99% |
| 杭州 | 12 | 259 | 100% |
| 哈尔滨 | 3 | 73 | 100% |
| 合肥 | 8 | 195 | 100% |
| 呼和浩特 | 2 | 43 | 100% |
| 香港 | 10 | 97 | 96% |
| 济南 | 8 | 145 | 100% |
| 昆明 | 6 | 103 | 100% |
| 兰州 | 2 | 27 | 100% |
| 澳门 | 3 | 15 | 100% |
| 南昌 | 4 | 113 | 100% |
| 南京 | 14 | 249 | 100% |
| 南宁 | 5 | 95 | 100% |
| 宁波 | 9 | 179 | 100% |
| 青岛 | 8 | 176 | 100% |
| 上海 | 20 | 417 | 99% |
| 沈阳 | 6 | 144 | 100% |
| 深圳 | 17 | 350 | 100% |
| 石家庄 | 3 | 60 | 100% |
| 苏州 | 9 | 231 | 100% |
| 太原 | 2 | 46 | 100% |
| 天津 | 12 | 239 | 92% |
| 乌鲁木齐 | 2 | 22 | 91% |
| 武汉 | 13 | 289 | 100% |
| 无锡 | 5 | 89 | 100% |
| 厦门 | 5 | 92 | 62% |
| 西安 | 13 | 248 | 100% |
| 徐州 | 4 | 70 | 100% |
| 郑州 | 13 | 233 | 100% |

## 6. 结构与性能

- 城市/地区：37
- 线路：339
- 车站：6464
- Stop：7572
- 区间：7234
- 换乘：2558
- 首末班记录：14789
- OSM z10 底图：37 张城市拼接图（771 张源瓦片）
- HTML 文件大小：14970836 bytes（约 14.28 MB）
- 初始化（含 1 秒等待的测量值）：约 1236 ms
- 路线计算（20 次平均）：约 1.1 ms

## 7. 本次回归重点

- 非上海城市：北京 1.3× 放大 + 拖动、8× 放大并拖到边界，线路与底图均正常。
- 每条线路已合并为单条 SVG `<path>`，不再使用逐段 `<line>` 和 `vector-effect`。
- 时间输入保留原生 datetime-local，新增“选择”按钮与 24 小时/5 分钟面板；01:00 显示“首班前 / 首班 05:30”，徽章无空白。
- 每个城市使用单张拼接底图，避免 SVG 瓦片接缝。

## 8. 离线/安全验收

- `file://` 直接打开：通过
- 离线上下文：通过
- 无 `fetch` / `XMLHttpRequest` / WebSocket / CDN / 外部字体/图片：代码扫描通过
- 所有城市数据、票价、首末班、OSM 底图均在 HTML 内：构建产物检查通过
- iframe 嵌入：通过，不访问父页面，不修改父页面样式

## 9. 未通过/未验证项

- Firefox：本机 Playwright Firefox 启动时被 macOS 沙箱扩展拦截，未标记通过。
- iOS WKWebView / Android WebView：未在真实设备上跑；已通过 WebKit 桌面与移动视口检查。
- OSM 底图只有 z10：放大后会模糊。
- 完整列车时刻：只有首末班，候车按 3 分钟估算。
- 票价：官方 OD 矩阵时点值，不含未来政策、儿童票、月度累计等。
- 未收录城市：常州、东莞、佛山、绍兴、嘉兴、金华、洛阳、南通、芜湖、台州、泉州、三亚、温州等；未伪造数据。

## 10. 复现方式

```bash
python3 tools/build.py
python3 tools/validate.py
node tools/test_app.mjs
node tools/test_display.mjs
```
