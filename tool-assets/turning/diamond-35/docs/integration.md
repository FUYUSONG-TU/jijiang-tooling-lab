# 向机匠学院正式项目移植

本包只提供资产、局部坐标和装配接口，不连接微信账号、数据库或G代码引擎，也不确定机床轴配置。

## 先在浏览器验证

在本包根目录运行 `python -m http.server 8768`，打开 http://localhost:8768/preview/index.html 。Three.js与OrbitControls/GLTFLoader通过CDN加载0.169.0，模型和元数据从本地HTTP读取。不能用file://直接打开。

完整原样板HTML仍在项目根目录，仅新增移植模式入口。独立ZIP中的preview不依赖原预览器或原项目绝对路径。

## 加载模块

把models、metadata、lib复制到正式项目的静态资产目录，保留相对路径；或者通过createToolLibrary的assetBaseURL指定资源根目录。使用宿主项目同一份Three.js和同版本GLTFLoader，先与本包已测试的0.169.0对照，不向正式项目强制升级Three.js。

```js
import { loadToolModel, getToolTipPosition, getMountingReference,
  applyToolTransform, getToolTipWorldPosition, getToolComponents,
  disposeToolModel, TOOL_ID } from './lib/tool-loader.js';

const model = await loadToolModel(TOOL_ID, 'r04');
seat.add(model); // seat由正式项目提供；此示例父场景单位为mm
applyToolTransform(model, { position: [10, 0, 5], quaternion: [0, 0, 0, 1] });
const localTip = await getToolTipPosition(TOOL_ID, 'r04');
const mounting = await getMountingReference(TOOL_ID);
// 每次机床/刀座父节点变化后查询：会更新父矩阵。
const worldTip = getToolTipWorldPosition(model);
const collisionCandidates = getToolComponents(model); // 仅真实实体，不含UI辅助球
// 卸载：
disposeToolModel(model);
```

loadToolModel返回的根节点已经是mm/Z-up，内部conversion节点负责唯一的文件坐标换算。getToolTipPosition返回模型局部mm，getToolTipWorldPosition返回经过所有父节点变换的世界点。applyToolTransform支持position/quaternion/scale或16项列主序仿射矩阵，不把模型中心误用为刀尖。矩阵translation遵循模型父场景的mm约定，applyToolTransform只设置局部到父级的装配矩阵。

getMountingReference返回point、matrix和坐标系定义；本轮point为原点、默认matrix为单位矩阵，不冒充真实刀座标定。

## 更换版本

示例examples/install-tool.js实现createMountedTool(seat,variant,transform)，提供replaceVariant、getTipWorldPosition、getCollisionCandidates和dispose。replaceVariant先加载新版本并保留安装矩阵，再释放旧实例；并发切换只接纳最后一次结果，失败时保留当前刀具。新GLB和新元数据一同生效。

```js
import { createMountedTool } from './examples/install-tool.js';
const handle = await createMountedTool(seat, 'r02');
await handle.replaceVariant('r08');
const tip = handle.getTipWorldPosition();
handle.dispose();
```

不要只更改noseRadius JSON字段，也不要在r04模型上使用r08刀尖坐标。

## 与G代码引擎的边界

正式引擎应在单独适配层定义编程轴→物理轴→刀座装配的映射，随后只把刀座世界矩阵作用于模型。工具模块不读取G01、不解释X直径编程、不把model.position等同于机床指令位移。S205A实际轴方向、通道、刀补必须由正式项目的实机资料确定。

若宿主需要“让刀尖到达目标世界点”，应结合宿主已验证的刀座姿态和局部刀尖偏置求解安装平移，不能令刀杆原点直接等于目标刀尖点。

## 缓存和内存

createToolLibrary缓存元数据Promise及最多3个已知版本的GLB ArrayBuffer，同版本并发只发一次字节请求。每次加载重新解析为独立几何/材质实例，释放一个实例不会破坏其他实例。失败请求会从缓存移除以允许重试。

disposeToolModel去重释放该实例的geometry、material、texture并从父级移除，可重复调用；它不释放共享原始字节缓存。资源库不再使用时调用clearResourceCache。宿主自行添加的共享GPU资源不应挂在刀具子树里，否则会被视为实例所有并释放。

预览器按需渲染，手机视口默认用轻量材质，GLB的PBR材质保持不变。源文件及截图只供开发，无须随小程序运行包一起发布；运行时只需GLB、元数据、模块与宿主Three.js。

## 微信适配状态

| 路径 | 当前状态 | 正式项目需验证 |
|---|---|---|
| 云端Chromium桌面/390px触摸视口 | 自动化通过 | 不代表实体手机；需iOS/Android浏览器性能、旋转与内存实测 |
| 普通实体手机浏览器 | 未进行真机测试 | GPU帧率、首次加载、内存、后台切换、资源回收 |
| 微信原生WebGL | 未适配/未真机测试 | 使用正式项目已有canvas/Three适配层；wx.request或文件系统返回ArrayBuffer，适配GLTFLoader所需IO和API，不假定浏览器fetch/DOM存在 |
| 微信Web-view | 未进行微信真机测试 | HTTPS业务域名、CDN/CORS、iOS WKWebView与Android GPU、跨页通信和前后台生命周期 |

可通过createToolLibrary({loadArrayBuffer, fetchImpl, loaderFactory})注入平台IO与加载器。fetchImpl仍须提供元数据所需的ok/status/json响应；loadArrayBuffer须返回真正ArrayBuffer。这个注入点不是已完成的小程序原生适配器。

服务器配置application/octet-stream或model/gltf-binary、正确CORS、按模型版本/哈希设置缓存；元数据升级与GLB同时发布。若启用HTTP gzip，保留正确Content-Encoding，不需要额外解码器。

## 测试与再导出

运行 `python tests/verify_assets.py`；HTTP服务启动后运行 `node tests/verify_browser.cjs`（需要Playwright，优先当前系统Chromium；CHROMIUM_PATH可覆盖）。TOOL_PREVIEW_URL可设置完整资源根URL，末尾带/。

Blender4.3.2执行 `blender -b --python sources/standardize.py` 可从保留的三份原.blend再导出标准资源与metadata/tool.json；之后重新运行两组测试。sources/original/build_tool.py保留原参数化建模过程，默认输出到它所在目录的models/，不是本包models/，不会自动替换标准资源。

## 打包与独立解压验收

`python tests/package_assets.py` 默认把diamond-35-tool-package.zip写到资源目录的同级；可通过--output指定完整路径。运行 `node tests/verify_zip.cjs` 将解压到临时目录、核对manifest并启动独立HTTP源进行GLB加载验证，最后关闭服务并清理临时目录。若ZIP放在其他位置，用TOOL_PACKAGE_ZIP指定路径。这个测试不会部署或推送代码。
