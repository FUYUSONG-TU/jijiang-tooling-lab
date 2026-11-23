# 加载与S205工位类型集成

## 运行验证入口

从仓库根目录运行：

```
python -m http.server 8771
```

浏览器打开 `http://localhost:8771/demos/s205-tool-stations/`。Three.js、GLTFLoader与OrbitControls使用同一CDN版本0.169.0。普通file://无法可靠运行模块与JSON加载。

这是新增的资产/工位检视入口，不扩展任何G代码案例。原有35°资源、G01案例及仿真引擎入口保持不变。

## 资源与API

```
import {loadToolModel, getToolTipPosition, getMountingReference,
  getCuttingReferenceWorld, getComponents, disposeToolModel}
  from './tool-assets/s205-seven/lib/tools.js';
import {mountInStation, inspectStationClearance}
  from './tool-assets/s205-seven/lib/stations.js';

const model = await loadToolModel('twist-drill'); // 也接受JJ-TWIST-DRILL
scene.add(model); // 本例宿主世界单位mm
mountInStation(model, 'axial-static');
const worldReference = getCuttingReferenceWorld(model);
const report = inspectStationClearance(model);
const physicalMeshes = getComponents(model);
// 卸载
 disposeToolModel(model);
```

loadToolModel恢复毫米/Z-up后返回根节点。模型在父节点旋转/平移后，getCuttingReferenceWorld会更新父矩阵再把本地刃口点转换为世界点。安装原点由getMountingReference返回新Vector3，不能直接把后端原点放到目标切削点。

createToolLibrary支持baseURL、fetchImpl、loadArrayBuffer和loaderFactory注入。只缓存原始GLB字节及元数据，每次解析生成独立GPU资源；释放一个实例不会破坏其他实例。clearCache不自动卸载已存在模型，卸载需要disposeToolModel；dispose可重复调用。

### 工位兼容性

| 逻辑工位类型 | 允许工具 | 接口/能力 |
|---|---|---|
| gang-od | 外圆切槽、切断、外螺纹 | 方柄静止排刀座 |
| axial-static | 中心钻、麻花钻 | 圆柄轴向静止钻孔座 |
| axial-boring | 内孔镗杆 | 圆柄内孔刀座 |
| optional-driven | 整体硬质合金立铣刀 | 圆柄动力刀座；默认禁止，必须显式开启未核验示意 |

不兼容类型会抛出错误。**这些是示意类型ID，不是S205真实T号或厂家工位表。** 现有图能支持外圆/钻孔/内孔类别区分，不能证明S205某台配置具有动力头。绝不把铣刀放到静止钻孔座冒充铣削能力。

选择铣刀时，默认可检视实际模型；未开启条件示意时，工位装配会被阻止。只有调用`mountInStation(model,'optional-driven',{allowUnverifiedDriven:true})`或明确勾选页面选项，才显示条件动力刀座。返回actualMachineVerified始终为false。

### 装配方向和停放位置

- 方柄外圆工具：用实际cuttingReferencePoint对准(6,18,0)，矩阵`T=target−R×reference`，当前演示R为单位矩阵。柄朝径向外侧，工具停在Ø16棒料外部，不切削。
- 圆柱轴向工具：Rz(−90°)，本地−Y映射为机床教学轴向−a；用轴线前端量规点对准(36,0,0)，棒料端面在a=24，停放间隔12mm。
- 钻头的中心钻尖与主轴中心线重合；镗杆和铣刀的切削角可以偏离中心轴，不会为了让刃口点居中而错移刀杆中心线。
- 工位夹具根据mountingInterface的方柄截面或圆柄直径生成，与资产自身刀杆区分。

inspectStationClearance对真实GLB顶点和三角形中心做有限采样，检查当前停放位置与Ø16棒料、导套环域的明显干涉，另检查圆柄轴线方向/中心线。它没有计算装夹力、所有附件间的CAD实体包含或运动扫掠，也不提供机床运行许可。正确工位类型不代表真实S205位置、行程与安全联锁已核验。

## 微信小程序准备

资产已做移动端预算控制：单模型约105～156KiB，最多6844三角面，2～3个材质、0纹理，无动画、无外部Buffer、无Draco/Meshopt解码器。运行时只需models、metadata、catalog.json和lib，不应把.blend、脚本或截图放进小程序运行包。

原生微信需要复用正式项目自己的canvas/Three适配层，并给库注入IO，例如：

```
const library = createToolLibrary({
  baseURL: 'https://your-approved-domain/assets/s205-seven/',
  fetchImpl: async url => {
    const r = await requestJsonWithWx(String(url));
    return {ok:r.statusCode===200, status:r.statusCode, json:async()=>r.data};
  },
  loadArrayBuffer: url => requestArrayBufferWithWx(url),
  loaderFactory: () => new AdaptedGLTFLoader()
});
```

requestJsonWithWx/requestArrayBufferWithWx与AdaptedGLTFLoader是正式项目必须提供的适配实现，不是本轮已经接入微信的代码。需验证wx.request/文件系统ArrayBuffer、URL/TextDecoder等环境API、Three版本、资源域名/分包、前后台切换和释放。模型无纹理减少了Image/Blob依赖，但不能由此宣称原生微信已经兼容。

已进行云端Chromium移动视口测试；实体手机、微信原生WebGL及微信Web-view均仍未真机验证。Web-view另需验证HTTPS业务域名、iOS/Android GPU和生命周期。

## 再生成与验收

```
blender -b --python tool-assets/s205-seven/sources/generate_tools.py
blender -b --python tool-assets/s205-seven/tests/check_blender.py
blender -b --python tool-assets/s205-seven/tests/check_assembly.py
python tool-assets/s205-seven/tests/verify_glb.py
node tool-assets/s205-seven/tests/verify_browser.cjs
```

浏览器测试需要先启动8771服务、安装Playwright及Chromium。源文件与测试均以自身位置解析资源目录。生成脚本会导出7份独立GLB、7份JSON和7份可编辑.blend，不会改动原35°文件，也不会提交Git。
