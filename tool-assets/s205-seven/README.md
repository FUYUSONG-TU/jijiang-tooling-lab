# 七类实体切削刀具资源

7种工具，每种1份独立GLB，另附独立JSON、Blender源文件与可复现生成脚本。不是占位方块，不包含新G代码教学案例。原35°菱形车刀及其三个R角GLB保持不变。

入口：仓库根目录启动 `python -m http.server 8771`，打开 http://localhost:8771/demos/s205-tool-stations/ 。

目录：models/实体GLB；metadata/逐刀元数据；sources/Blender与生成脚本；lib/加载和工位接口；tests/检查脚本；reports/实际测试与多视图；docs/尺寸、来源、集成与验证边界。

尺寸全部为教学默认值，不是厂家图纸核验值。工位类型限制已实现，但真实S205刀号、位置、选配及轴配置未核验。铣刀仅允许条件动力头示意，不能装进静止钻孔位。微信原生/Web-view仍待真机适配与验证。
