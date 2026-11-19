from pathlib import Path
import json,hashlib,zipfile,subprocess
from PIL import Image,ImageDraw,ImageFont
root=Path(__file__).resolve().parent
report=json.loads((root/'reports/verification.json').read_text());meta=json.loads((root/'assets/metadata/tool.json').read_text())
originals=json.loads((root/'reports/original-hashes.json').read_text());unchanged=all(Path(p).exists()and hashlib.sha256(Path(p).read_bytes()).hexdigest()==sha for p,sha in originals.items());assert unchanged
for v in meta['noseRadiusVariants'].values():assert hashlib.sha256((root/'assets'/v['modelPath']).read_bytes()).hexdigest()==v['sha256']
(root/'reports/preservation.json').write_text(json.dumps({'originalFilesChecked':len(originals),'unchanged':unchanged,'glbCopiesMatchPackage':True,'gitOperationsPerformed':False},ensure_ascii=False,indent=2))
fontpath='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc';font=ImageFont.truetype(fontpath,23,index=2)
img=Image.new('RGB',(1836,640),'#0b1118');draw=ImageDraw.Draw(img)
for i,(file,title)in enumerate([('real-close.png','真实GLB刀具 · R0.4'),('simple-close.png','原35°简化轮廓 · 对比')]):
 source=Image.open(root/'reports'/file).crop((288,198,1194,768));img.paste(source,(i*918+6,47));draw.text((i*918+15,8),title,font=font,fill='#7ce4d1')
img.save(root/'reports/comparison.jpg',quality=94)
small=[(r['variant'],len(r['failed']))for r in report['shallowSweeps']if r['expected']=='small-stock-guide-interference']
first=report['firstLoad'];loads=[v['loadMs']for v in report['variants']]
text=f'''# 35°真实刀具 G01 走心机独立教学 Demo

## 打开与文件

目录：`/workspace/g01-real-tool-demo`。入口`index.html`，渲染代码`app.js`，纯运动状态`motion.js`，安装/采样适配`real-tool-adapter.js`。assets/是标准刀具包中原样复制的3份GLB、元数据及加载模块，未重新建模。Three.js与OrbitControls/GLTFLoader统一使用CDN版本0.169.0，与原刀具资源及Swiss Demo一致。

当前服务：**http://localhost:8770/**。需在当前云环境浏览器打开，或把8770端口转发到本机。如下载Demo，在目录中运行`python -m http.server 8770`再访问相同地址；不要用file://直接打开。CDN库需要网络。

本轮按用户最新澄清只做新独立Demo；未关联微信、正式项目或17个案例。没有Go、API、数据库、会员、支付及登录变更，没有Git提交/推送/部署。

## 实现内容

- 实际GLTFLoader加载35°专业样板，支持R0.2/R0.4/R0.8，始终计为1把刀的3个参数变体。
- 主轴箱、旋转夹头、棒料、固定导套、排刀装配及U形演示刀座。U座围绕后部10×10刀杆截面搭建，窗口接触为设计装配接触，不是厂家安装标定。
- G01列表、高亮、中文解释、播放/暂停、单步、重置、0.5×/1×/2×、可回拖时间轴与代码点击跳转。
- 棒料直径、目标直径、加工长度、进给可调；调整后同步生成程序、轨迹、目标刀位及工件形状并复位。
- 物理运动 / 相对工件视图、整机 / 刀尖近景 / 正视 / 轴向视角、OrbitControls触摸旋转、双指缩放与平移。
- 真实刀具和原Swiss Demo的35°简化轮廓对比。比较截图采用相同参数、同一程序时刻与同一相机；两者不是已标定为相同主偏角的生产刀具。

## 坐标与安装

工具资源原始GLB为米制/Y-up；复用加载模块只换算一次到毫米/Z-up。该工具局部系与场景教学物理系(a,r,c)不同。场景以Three的(x,y,z)分别表示(a,r,c)，c为切削平面法向。

演示安装姿态为`R = Rz(+18°)`，将样板原刀片平面旋转−18°的前端转向径向下方。此值不是实机主偏角、左右手或机床安装参数。

每版从元数据读取自己的刀尖`t_R`。给定物理目标刀尖`q = (6, X/2, 0)`，模型点p在物理系的位置为：

`p物理 = q + R × (p − t_R)`

模型安装根的局部矩阵是`[ R | −R×t_R ]`，父排刀节点平移到q。安装参考原点m=(0,0,0)随同一矩阵变换；U形演示座使用同一矩阵包围刀杆后部。没有把模型中心或后端原点当作刀尖。

更换鼻圆会加载另一份GLB、读取新刀尖并重算`−R×t_R`，保持当前程序时刻和刀尖目标不跳变。换下模型释放几何、PBR/轻量材质及刀座临时资源。复制的原加载模块仍提供按需加载、最多3版字节缓存与实例释放。

## 走心机教学运动

工件坐标Z0为右端面，负Z指向夹持端；X按直径表示，r=X/2。a为向出料方向为正的教学几何轴，不代表S205A实际轴名。

物理刀位固定a=6，棒料前端`a_front=6−Z`，主轴箱参考点`a_head=a_front−110`。因此G01 Z减小由主轴箱/棒料向+a送出实现；刀具不做物理轴向进给，只有径向进给。主轴和棒料共转，暂停时一起停止。

导套前端a=0、后端a=−8，教学孔半径=棒料半径+0.15，外部半径18/19。程序退刀后停留，不把细径段回拉穿过导套。导套类型按固定式简化，没有核验S205A真实配置。

相对视图对整机统一施加`δ=−(a_front−4)`的轴向平移，工件端面固定在4，显示刀尖a=4+Z。导套在画面中移动仅来自参考系变换，与物理进给不同。青线显示相对工件的G01轨迹，灰虚线为G00。

程序由参数生成，代码终点与同一运动段数据驱动刀尖/棒料，非无关联动画。进给距离按实际径向/轴向距离计算，教学时间压缩8倍，再乘播放倍率。只执行本页生成的教学程序，不是任意G代码解释器；没有写入未经核实的FANUC/S205A初始化、刀补或主轴命令，不可上机。

## 材料与干涉近似

材料是旋转台阶包络：刀尖在纵向G01越过端面后，已扫过区间变为目标半径。工件用可复用圆柱网格的真实尺寸缩放更新，避免每帧重新分配/上传几何；退刀保留结果，回拖时间轴可恢复。

没有精确布尔切削、刃口圆弧肩部过渡、切屑、弹性、切削力或刀尖半径补偿。模型内记录的是有限网格上的刃口参考点，不代表所有安装姿态下通用的真实切削接触点。

碰撞检查使用GLB表面的三角形细分采样，三角形最大边按1mm步长细分且至少2等分，按角色分开；数据用Float32/Uint8/Uint32紧凑缓冲存储。当前r04有{first['samples']:,}个去重采样点、缓冲约{first['sampleBufferBytes']/1024/1024:.2f}MiB。根据正径向和当前6～20mm棒料/19mm导套外半径，静态保守剔除不可能接触的远端点，再做动态包络检查，没有减少鼻圆几何。

分别检测刀杆/刀头、垫座、紧固件、U座进入材料、刀片异常进入及导套环域干涉。材料穿入阈值0.025mm是教学比较容差，不是机床精度。圆弧与35°刃型在端面入切/肩部附近的未解析接触带按`R+(切深+R)×tan17.5°+0.12`宽度单列，不能将该带说成精确去除或“完全无干涉”。

这是离散表面采样，不覆盖所有实体包容、连续扫掠与真实支承结构。检测到非切削结构干涉后停止播放，但允许暂停、跳转和单步查看问题位置。红点是首个检测到的干涉采样位置。

## 实测结果

最终报告：reports/verification.json。带断言测试verify.cjs已通过：

- 三版默认Ø16→Ø15.5、长度24，以及Ø20→Ø19.5、长度45，各81时刻，共**{report['shallowStates']}个浅切轨迹状态**，未检出所定义接触带之外的非预期干涉。
- Ø6→Ø5.5、长度8，共{report['smallStockStates']}个边界状态。三版均检测到导套干涉，命中状态数分别为{small}；没有将滑块全范围伪称安全。
- Ø16→Ø12、长度24，三版各81时刻，检测到刀头和垫座进入未去除材料。命中状态数分别为{[(v['variant'],v['failedStates'])for v in report['deep']]}。真实播放自动暂停断言通过。
- 刀尖装配误差在所测状态为0（数值打印精度）；物理/相对两视图保持同一程序坐标，实际GLB刀尖与预期世界目标一致。不同R角读到不同局部刀尖，换R时程序坐标与刀尖目标保持不变。
- 材料段长度/半径与状态一致，参数改变更新G01代码并复位；播放、暂停、单步、重置、速度调节通过。主轴与棒料共同旋转、物理刀位轴向不动通过。
- 人为把刀位放到导套内，检测器能报告导套干涉；旧GLB实例更换后已释放、从父级移除。
- 页面JavaScript错误0，所记录HTTP错误0；复制的三份GLB哈希与原包一致。{len(originals)}个原文件哈希核对未变化（见reports/preservation.json）。

## 加载与手机性能

每份GLB约517KiB、5个资产网格、4个PBR材质、8416～8422三角面，三版合计{sum(v['bytes']for v in meta['noseRadiusVariants'].values()):,}字节。演示刀座和场景几何另计，没有把它们算作新增专业刀具。

本次云端Chromium：首次从GLB加载开始到装配/采样结束约{first['loadMs']/1000:.2f}s，缓存条件下三版切换约{min(loads):.0f}～{max(loads):.0f}ms。该墙钟测量可能包含并发首帧渲染开销，不是纯网络下载速度。

390×844移动视口下触摸旋转、双指缩放及无横向溢出通过；轻量材质、持续加工动画且开启采样检查时实测约**{report['cloudMobileFps']:.1f} FPS**。此为本次云端环境数据，仍有性能优化空间，不能声称全部手机流畅。已经采用全场景轻量材质、按需静止绘制、紧凑采样缓冲、保守候选剔除，以及棒料网格复用。

**普通实体手机未真机验证；微信原生WebGL和微信Web-view均未接入或真机验证。** 本轮按最新要求不寻找正式小程序、也不推断其渲染方式。日后原生方案需要项目自身的canvas/IO/GLTFLoader适配；Web-view需要HTTPS业务域名和iOS/Android生命周期/内存测试。

## 是否建议正式替换

**暂不建议直接替换正式刀具。** 本轮证明实际GLB可以按版本刀尖装配，正确跟随典型走心机教学状态，并完成默认浅切演示；没有证明刀头/垫座在深切或小棒料下具有足够避让、后角和支承。

尚需解决：实际刀头与垫座结构/后角/悬伸图纸核验、导套外形与刀位距离、刀座装配与行程、刀尖接触/刀补定义、精确圆弧去除、连续实体碰撞、S205A轴和控制器配置，以及实体手机性能。当前不通过改动刀尖位置或隐藏零件掩盖干涉。

## 截图与复现

reports/comparison.jpg：真实刀具与旧简化轮廓的同状态/同视角对照。另有real.png整机、real-close.png刀尖、relative.png相对视图、deep-interference.png干涉及mobile.png移动布局。

启动服务后运行 `node /workspace/g01-real-tool-demo/verify.cjs` 可复现实验断言，需要环境已有的Playwright和/usr/bin/chromium。build_report.py从实际JSON生成本报告及对比图。代码和报告仅在新Demo目录内。
'''
(root/'README.md').write_text(text)
with zipfile.ZipFile('/workspace/g01-real-tool-demo.zip','w',zipfile.ZIP_DEFLATED)as z:
 for f in root.rglob('*'):
  if f.is_file()and f.suffix not in ['.log','.pyc']:z.write(f,Path('g01-real-tool-demo')/f.relative_to(root))
print(json.dumps({'originalsUnchanged':unchanged,'report':str(root/'README.md'),'zip':'/workspace/g01-real-tool-demo.zip'},ensure_ascii=False))
