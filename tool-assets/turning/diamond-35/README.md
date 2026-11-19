# 35°菱形外圆车刀 · 标准移植资源包

专业模型数量：1。r02/r04/r08为同一把刀的鼻圆参数变体；不包含旧六类简化教学刀具。

- models/：3份GLB，米制/Y-up。
- metadata/tool.json：统一mm/Z-up元数据，逐版本刀尖、圆弧中心、尺寸与包围盒。
- lib/tool-loader.js：加载、缓存、装配、刀尖转换、碰撞候选与释放接口。
- examples/install-tool.js：换版本保留装配变换的宿主接入示例。
- preview/index.html：GLTFLoader实际移植验证；文件大小、网格与三角面统计。
- sources/：从现有模型标准化导出的脚本、原.blend与原参数化脚本。
- docs/：尺寸/坐标、移植说明、验证报告。
- tests/：独立GLB解析及浏览器/接口断言。
- reports/：实际自动化结果及截图。
- references/：来源与权限状态记录，未包含再分发授权不明的原图。

运行 `python -m http.server 8768`，浏览器打开 http://localhost:8768/preview/index.html 。CDN Three.js0.169.0需联网。

尺寸为教学近似值，不是厂家图纸验证结果；微信原生WebGL和微信Web-view均待真机验证。详情见docs/integration.md。
