from pathlib import Path
import json,hashlib,zipfile,gzip
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];repo=R.parents[1];qa=json.loads((R/'reports/glb-validation.json').read_text());browser=json.loads((R/'reports/browser-validation.json').read_text());catalog=json.loads((R/'catalog.json').read_text());assert qa['passed']and browser['passed']and browser['completedAndReloaded']==7
baseline=json.loads((R/'reports/baseline-hashes.json').read_text());changes=[f for f,h in baseline.items()if not(repo/f).is_file()or hashlib.sha256((repo/f).read_bytes()).hexdigest()!=h];assert not changes,changes
(R/'reports/preservation.json').write_text(json.dumps({'existingFilesChecked':len(baseline),'unchanged':True,'existing35DegreeGlbsUnchanged':True,'newGcodeCases':0,'gitCommitPushOrDeployPerformed':False},ensure_ascii=False,indent=2))
refs=[]
for i in [1,3,5]:
 f=repo/'references/tooling'/f'{i}-照片-{i}.jpg';refs.append({'file':str(f.relative_to(repo)),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'redistributionPermission':'未确认，本新增包不含原图'})
(R/'reports/reference-provenance.json').write_text(json.dumps(refs,ensure_ascii=False,indent=2))
font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',23,index=2)
for tool in catalog['tools']:
 sheet=Image.new('RGB',(1240,1020),'#0b121a');draw=ImageDraw.Draw(sheet);draw.text((15,5),tool['toolName']+' · GLB四视图',font=font,fill='#81e5d0')
 for j,view in enumerate(['iso','top','front','side']):
  im=Image.open(R/'reports'/f"{tool['toolType']}-{view}.png");im.thumbnail((600,460));sheet.paste(im,(10+j%2*620,55+j//2*480))
 sheet.save(R/'reports'/f"{tool['toolType']}-four-views.jpg",quality=92)
allImage=Image.new('RGB',(1500,1280),'#0b121a');draw=ImageDraw.Draw(allImage)
for i,tool in enumerate(catalog['tools']):
 x=(i%3)*500;y=(i//3)*420;draw.text((x+10,y+5),tool['toolName'],font=font,fill='#81e5d0');im=Image.open(R/'reports'/f"{tool['toolType']}-close.png");im.thumbnail((490,370));allImage.paste(im,(x+5,y+43))
allImage.save(R/'reports/seven-tools-overview.jpg',quality=94)
# package only current sources, not Blender autosave copies.
for f in(R/'sources').glob('*.blend1'):f.unlink()
rows=[]
for r in qa['results']:
 t=next(t for t in catalog['tools']if t['toolType']==r['toolType']);rows.append(f"| {t['toolName']} | {r['bytes']/1024:.1f} | {r['triangles']} | {r['parts']} | {r['drawPrimitives']} |")
mobile=browser['mobilePerformance'];tipMax=max(r['referenceSurfaceErrorMm']for r in qa['results']);bboxMax=max(r['bboxMaxErrorMm']for r in qa['results'])
report=f'''# 七种实体刀具实际验收报告

## 已完成的模型

七份独立GLB均存在并通过独立解析及Three.js GLTFLoader重载，才记为完成。各自的JSON和.blend位于metadata/与sources/；同一个sources/generate_tools.py可复现全部七把。本轮没有新增第八种刀具或G代码案例，原35°的3个鼻圆版本没有变化。

| 工具 | GLB KiB | 三角面 | 实体部件 | 绘制网格 |
|---|---:|---:|---:|---:|
'''+ '\n'.join(rows)+f'''

总GLB大小 **{qa['totalGlbBytes']:,}字节（{qa['totalGlbBytes']/1024/1024:.3f}MiB）**。每把0纹理、2～3个PBR材质，未引入压缩解码器或外部Buffer。螺旋槽是实际实体凹槽，切槽/切断刀有真实让位与断屑槽，螺纹刀有中心孔、凹面和独立座体，紧固件有真实驱动凹槽。夹持工位与刀具本体分开。

## 几何检查

- GLB2头、长度、JSON/BIN、索引范围、实际面数与SHA-256核对通过；所有顶点/法线有限，法线长度约1。
- 包围盒与元数据最大偏差{bboxMax:.9f}mm，刃口参考点至重载网格表面最大距离{tipMax:.9f}mm。后端安装原点位于真实后端截面。
- 三角形退化计数0；源文件所有部件非流形边0、有向体积为正。
- 单部件BVH自交检查排除共享顶点的相邻三角形后候选0。不同部件的所选刀杆/刀片表面求交候选0。
- 补充的部件装配检查使用三方向射线多数判定：未检出顶点严格进入其他部件；距界面0.002mm以内为接触。座面、端面及螺丝座接触有意保留。
- 这些是网格/有限采样检查，不是认证CAD实体求交、连续扫掠或夹紧力证明，不能替代制造商尺寸图。

## 多角度视觉检查

每把模型已从等轴测、俯视、端面、侧视和刃部近景实际截图，并完成工位截图，见reports/*-four-views.jpg和*-close.png。逐把检视确认：外圆刀有独立刀片及夹紧层次；切断刀的薄刀板与厚安装体分开；内孔杆前部偏置；钻/铣刀槽凹入并保留芯部，没有用装饰螺旋或占位盒替代。

## 工位验证

7把均通过类型相符的演示工位停放检查，工件与导套采样干涉为0。轴向工具中心轴方向/中心线误差低于1e-8（数学变换误差，不是制造精度）。钻尖和铣刀/镗刀偏置切削角没有混用。

共检查每把3种错误工位类型，均拒绝。铣刀默认装配被动力选配锁阻止；显式允许后仅进入条件动力座，不进入静止钻孔座。人为把工具移入棒料后检测器能检出干涉。装配坐标在有旋转和平移父节点时保持正确。

**实际S205工位号、位置、刀架接口、动力选配、行程和安全联锁仍未核实。** 参考图为通用排刀图，不能称为厂家S205配置图。本轮完成的是可复用工位类型接口和检视场景，不是给真实机床排刀认证。

## 移动与生命周期

云端Chromium390×844视口下，触摸旋转、双指缩放和无横向溢出通过。7种模型轻量材质单工具检视实测约 **{min(x['fps']for x in mobile):.1f}～{max(x['fps']for x in mobile):.1f}FPS**；这是本次云端浏览器测量，非微信或实体手机保证。完整结果见reports/browser-validation.json。

同工具多个实例的GPU几何不共享所有权；重复释放安全，释放一个实例后另一个仍可使用。缓存仅原始字节/元数据，选中工具才解析显示；切换时释放旧几何、PBR与轻量材质及辅助线。

**实体手机、微信原生WebGL及微信Web-view均未真机验证。** 资产规模已控制，但仍需正式宿主的canvas/IO/Three适配与内存生命周期检查，不能把浏览器通过当作原生微信兼容。

## 保留与限制

核对原仓库{len(baseline)}个已跟踪文件哈希均未变化，包括35° GLB及旧案例。没有改后端、数据库、支付、登录、会员，没有Git提交、推送或部署。

仍待专业审核：厂家型号和全部实际尺寸/公差、后角与刃磨、真实左右手/旋转方向、螺距/完整牙型、刀座支承和压紧、切断允许伸出、镗杆最小孔径、铣刀中心切削能力、实际S205配置。螺纹没有伪装成精确螺纹啮合；钻尖横刃和铣刀端部磨削为教学近似，不能宣称制造级准确。
'''
(R/'docs/verification.md').write_text(report)
# No generated user reference photographs are included.
files=[]
for folder in [R,repo/'demos/s205-tool-stations']:
 files.extend(f for f in folder.rglob('*')if f.is_file()and'__pycache__'not in f.parts and f.suffix not in ['.blend1','.log','.zip','.pyc']and f.name!='delivery-manifest.json')
manifest={'modelVersion':'1.0.0','newToolCount':7,'files':[{'path':str(f.relative_to(repo)),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}for f in sorted(files)]};(R/'delivery-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2));files.append(R/'delivery-manifest.json')
zipPath=repo/'s205-seven-tool-assets.zip'
with zipfile.ZipFile(zipPath,'w',zipfile.ZIP_DEFLATED)as z:
 for f in files:z.write(f,f.relative_to(repo))
with zipfile.ZipFile(zipPath)as z:assert z.testzip()is None
print(json.dumps({'models':7,'totalGlbBytes':qa['totalGlbBytes'],'package':str(zipPath),'packageBytes':zipPath.stat().st_size,'originalsUnchanged':True},ensure_ascii=False))
