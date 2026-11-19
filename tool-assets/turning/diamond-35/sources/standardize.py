"""Preserve existing geometry. Blender 4.3: bake original assembly, rebase to rear shank center, export metres/Y-up.
Run: blender -b --python sources/standardize.py
"""
import bpy, json, math, hashlib, bmesh
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1];ORIGINAL=ROOT/'sources/original'
ref=Vector((0,65,-5));all_variants={}
def bounds(points):
 lo=[min(v[k] for v in points) for k in range(3)];hi=[max(v[k] for v in points) for k in range(3)];return {'min':lo,'max':hi,'size':[hi[i]-lo[i] for i in range(3)]}
for radius,key in [(.2,'r02'),(.4,'r04'),(.8,'r08')]:
 bpy.ops.wm.open_mainfile(filepath=str(ORIGINAL/f'tool35-r{radius:.1f}.blend'))
 scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
 old=json.loads((ORIGINAL/f'tool35-r{radius:.1f}.json').read_text());qa=json.loads((ORIGINAL/f'quality-r{radius:.1f}.json').read_text())
 meshes=[o for o in scene.objects if o.type=='MESH'];points=[];component_data={};canonical={}
 # Original parent scales design mm to m. Bake the evaluated world pose, undo that scale, then shift datum.
 for o in meshes:
  points_mm=[o.matrix_world@v.co*1000-ref for v in o.data.vertices];canonical[o.name]=points_mm;points+=points_mm
  component_data[o.name]={'role':o.get('componentRole'),'boundingBox':bounds(points_mm),'vertexCountBeforeExport':len(points_mm)}
  o.parent=None;o.matrix_world.identity()
  for v,p in zip(o.data.vertices,points_mm):v.co=p*.001
  o.data.update()
 for o in list(scene.objects):
  if o.type!='MESH':bpy.data.objects.remove(o,do_unlink=True)
 tip=Vector(old['cuttingTipPosition'])-ref;nominal=Vector(old['nominalNoseArcApex'])-ref
 # For this existing rotated rhombus the first corner's fillet center lies on its long bisector.
 cy=-10+radius/math.sin(math.radians(17.5));angle=math.radians(-18)
 center=Vector((-1-cy*math.sin(angle),-5+cy*math.cos(angle),1))-ref
 source_tip_error=min((p-tip).length for p in canonical['Carbide_Insert_35deg'])
 audit={}
 for o in meshes:
  bm=bmesh.new();bm.from_mesh(o.data);audit[o.name]={'nonManifoldEdges':sum(not e.is_manifold for e in bm.edges),'positiveVolume':bm.calc_volume(signed=True)>0,'finiteNormals':all(math.isfinite(c) for f in bm.faces for c in f.normal)};bm.free()
 # Regression-check several potentially penetrating pairs; shared contact planes remain separate.
 def tree(name):
  o=next(o for o in meshes if o.name==name);return BVHTree.FromPolygons([v.co for v in o.data.vertices],[list(f.vertices) for f in o.data.polygons])
 pairs=[('Holder_Main','Carbide_Insert_35deg'),('Holder_Main','Screw_Head'),('Holder_Main','Screw_Shaft'),('Insert_Seat','Screw_Head'),('Insert_Seat','Screw_Shaft'),('Carbide_Insert_35deg','Screw_Head'),('Carbide_Insert_35deg','Screw_Shaft')]
 surface={a+'/'+b:len(tree(a).overlap(tree(b))) for a,b in pairs}
 for o in meshes:
  o['geometryUnits']='metres';o['toolId']=old['toolId'];o['modelVersion']='2.0.0';o['variant']=key
  o['dimensionVerification']='教学近似尺寸，非厂家核验'
 filepath=ROOT/'models'/f'diamond-35-{key}.glb'
 bpy.ops.export_scene.gltf(filepath=str(filepath),export_format='GLB',export_yup=True,export_extras=True,export_cameras=False,export_lights=False)
 insert_pts=canonical['Carbide_Insert_35deg'];holder=component_data['Holder_Main']['boundingBox']
 all_variants[key]={'noseRadius':radius,'modelPath':f'models/{filepath.name}','cuttingTipPosition':list(tip),'noseArcCenter':list(center),'nominalNoseArcApex':list(nominal),'virtualSharpTipPosition':list(Vector(old['virtualSharpTipPosition'])-ref),'boundingBox':bounds(points),'holderDimensions':{'width':holder['size'][0],'height':holder['size'][2],'length':holder['size'][1],'rearShankDatumLength':65},'insertThickness':bounds(insert_pts)['size'][2],'insertInstallation':{'centerXY':[-1-ref.x,-5-ref.y],'bottomZ':-1.6-ref.z,'topZ':1-ref.z,'planRotationDegrees':-18,'matrixColumnMajor':[math.cos(angle),math.sin(angle),0,0,-math.sin(angle),math.cos(angle),0,0,0,0,1,0,-1-ref.x,-5-ref.y,0-ref.z,1]},'components':component_data,'sourceTipVertexErrorMm':source_tip_error,'bytes':filepath.stat().st_size,'sha256':hashlib.sha256(filepath.read_bytes()).hexdigest(),'sourceQA':{'meshes':audit,'surfaceIntersectionCounts':surface,'contactPlanes':{'holderSeatFloorZ':-2.2-ref.z,'seatBottomZ':-2.2-ref.z,'seatTopZ':-1.6-ref.z,'insertBottomZ':-1.6-ref.z},'limitations':qa['limitations']}}
identity=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]
meta={'schemaVersion':'2.0','modelVersion':'2.0.0','toolId':'JJ-OD35-SAMPLE-001','toolName':'35°菱形外圆车刀 · 可移植教学样板','toolCategory':'external-turning','professionalToolCount':1,'insertShape':'35°菱形 / V形，ISO型号待确认','insertIncludedAngle':35,'approachAngle':None,'hand':None,'geometryUnits':{'metadata':'mm','glb':'m / glTF2 Y-up','loaderOutput':'mm / Z-up','glbToModelScale':1000,'conversionMatrixColumnMajor':[1000,0,0,0,0,0,1000,0,0,-1000,0,0,0,0,0,1]},'localCoordinateSystem':{'handedness':'right','origin':'刀杆后端截面中心（演示安装基准）','x':'+X 沿刀杆宽度','y':'+Y 从刀头指向刀杆后端；后端Y=0','z':'+Z 从刀杆底面指向刀片顶面','cuttingDirectionDescription':'刀片前端位于负Y；非机床进给方向','originalToStandardOffsetMm':list(-ref),'insertNoseUnitVector':[math.sin(math.radians(-18)),-math.cos(math.radians(-18)),0],'insertTopNormal':[0,0,1]},'mountingReferencePoint':[0,0,0],'mountingTransformMatrixColumnMajor':identity,'defaultVariant':'r04','holderDimensions':all_variants['r04']['holderDimensions'],'cuttingTipPosition':all_variants['r04']['cuttingTipPosition'],'noseArcCenter':all_variants['r04']['noseArcCenter'],'boundingBox':all_variants['r04']['boundingBox'],'noseRadiusVariants':all_variants,'modelPaths':{k:v['modelPath'] for k,v in all_variants.items()},'referenceImages':[{'source':'用户提供第5张拼图，第二排第四格','originalFile':'5-照片-5.jpg','sha256':json.loads((ORIGINAL/'reference-source.json').read_text())['sha256'],'redistributionStatus':'原图再分发授权未确认，仅记录来源，资源包不包含图片','distributed':False}],'verificationStatus':{'geometry':'程序构造及导出一致性检查；非制造商认证','dimensions':'全部线性尺寸为教学近似默认值，非图片测量值，非厂家核验','includedAngle':'任务与图片标签35°，解析菱形构造；有限网格含圆弧与刃口倒角','hiddenStructures':'刀座背面/垫座/螺丝内部为演示重建','machineAxes':'不定义S205A机床轴配置','manualReviewRequired':old['unconfirmed']},'collisionInterface':{'components':'按componentRole和独立mesh名称获取；未来可替换CAD碰撞包络','algorithmIncluded':False,'contactIsNotPenetration':True},'compatibility':{'testedThreeVersion':'0.169.0','webBrowser':'见reports/browser.json，不等于物理手机验证','wechatNativeWebGL':'待适配小程序canvas、加载器IO和GLB解析，未真机测试','wechatWebView':'待HTTPS业务域名、包体、iOS/Android性能和生命周期真机验证'}}
(ROOT/'metadata/tool.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
print('已标准化导出一把刀的三个鼻圆版本，总GLB字节',sum(v['bytes'] for v in all_variants.values()))
