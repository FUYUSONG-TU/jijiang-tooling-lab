"""Blender 4.3: one reference-led 35° tool, millimetre design coordinates.
All dimensions except the labelled 35° included angle are unverified demo defaults.
Run: blender -b --python build_tool.py -- --radius 0.4
"""
import bpy, math, json, sys, argparse, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from pathlib import Path
ROOT=Path(__file__).resolve().parent
arg=argparse.ArgumentParser();arg.add_argument('--radius',type=float,default=.4);args=arg.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
R=args.radius
if not .1<=R<=.8: raise ValueError('Demo nose radius must be 0.1..0.8 mm')
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
materials={}
def material(name,color,metal,rough):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Metallic'].default_value=metal;bs.inputs['Roughness'].default_value=rough;materials[name]=m;return m
steel=material('磨削钢刀杆 / 颜色参照图片',(.39,.45,.51),.83,.28)
seatmat=material('刀片垫座 / 结构演示',(.14,.18,.22),.78,.27)
carbide=material('金色硬质合金涂层 / 未确认牌号',(.72,.45,.13),.8,.23)
screwmat=material('黑色紧固螺丝',(.055,.068,.08),.82,.23)
def active(o): bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o

def bevel(o,amount=.15,seg=3):
 active(o);m=o.modifiers.new('实际边缘倒角','BEVEL');m.width=amount;m.segments=seg;bpy.ops.object.modifier_apply(modifier=m.name)

def normals(o):
 active(o);m=o.modifiers.new('加权表面法线','WEIGHTED_NORMAL');m.keep_sharp=True;bpy.ops.object.modifier_apply(modifier=m.name)

def poly(name,pts,z0,z1,mat=None):
 n=len(pts);verts=[(x,y,z) for z in [z0,z1] for x,y in pts];faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)];me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o)
 if mat:o.data.materials.append(mat)
 return o

def boolean(o,cutter,operation='DIFFERENCE'):
 active(o);m=o.modifiers.new('真实布尔加工','BOOLEAN');m.operation=operation;m.solver='EXACT';m.object=cutter;bpy.ops.object.modifier_apply(modifier=m.name);bpy.data.objects.remove(cutter,do_unlink=True)

def cylinder(name,r,z0,z1,x=-1,y=-5,mat=None):
 bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=r,depth=z1-z0,location=(x,y,(z0+z1)/2));o=bpy.context.object;o.name=name
 if mat:o.data.materials.append(mat)
 return o

def cone(name,r0,r1,z0,z1):
 bpy.ops.mesh.primitive_cone_add(vertices=96,radius1=r0,radius2=r1,depth=z1-z0,location=(-1,-5,(z0+z1)/2));o=bpy.context.object;o.name=name;return o

ang=math.radians(-18);cx,cy=-1,-5
def transform(p):
 x,y=p;return (cx+x*math.cos(ang)-y*math.sin(ang),cy+x*math.sin(ang)+y*math.cos(ang))
# Exact 35° rhombus, filleted by analytic tangent-circle construction.
a=10;b=a*math.tan(math.radians(17.5));vertices=[(0,-a),(b,0),(0,a),(-b,0)]
def rounded(points,r):
 out=[];centers=[]
 for i,p in enumerate(points):
  p=Vector(p);prev=Vector(points[i-1]);nex=Vector(points[(i+1)%len(points)]);u=(prev-p).normalized();v=(nex-p).normalized();alpha=math.acos(max(-1,min(1,u.dot(v))));center=p+(u+v).normalized()*(r/math.sin(alpha/2));A=p+u*(r/math.tan(alpha/2));B=p+v*(r/math.tan(alpha/2));t1=math.atan2(A.y-center.y,A.x-center.x);t2=math.atan2(B.y-center.y,B.x-center.x)
  while t2<t1:t2+=2*math.pi
  if t2-t1>math.pi: t2-=2*math.pi
  for k in range(25):
   t=t1+(t2-t1)*k/24;out.append((center.x+r*math.cos(t),center.y+r*math.sin(t)))
  centers.append(tuple(center))
 return out,centers
outline,centers=rounded(vertices,R);outline=[transform(p) for p in outline]
# Main bar is an extruded chamfered polygon, fused to a swept, asymmetric head.
C0=Vector(centers[0]);V0=Vector(vertices[0]);active_nose=transform(C0+(V0-C0).normalized()*R);tx,ty=active_nose
body=poly('Holder_Main',[(-5,65),(-5,-5),(-4.9,-9.5),(tx-.1,ty+.9),(tx+.65,ty+1.2),(5,-1),(5,65)],-10,0,steel)
bevel(body,.22,4)
pocket,unused=rounded([(x*1.025,y*1.025) for x,y in vertices],R+.05);pocket=[transform(p) for p in pocket]
boolean(body,poly('真实开放式刀座腔',pocket,-2.2,3))
boolean(body,cylinder('未确认规格的盲孔',1.09,-5,-1.7))
# Tiny head machining relief: physical V-grooves on the bar neck, not an image decal.
for y in [9,61.8]:
 boolean(body,poly('肩部磨削分界',[(-5.4,y),(5.4,y),(5.4,y+.12),(-5.4,y+.12)],-.035,.1))
normals(body)
seatpts,_=rounded([(x*.96,y*.96) for x,y in vertices],max(.15,R*.9));seat=poly('Insert_Seat',[transform(p) for p in seatpts],-2.2,-1.6,seatmat);boolean(seat,cylinder('垫座通孔',1.13,-3,0));bevel(seat,.035,2);normals(seat)
insert=poly('Carbide_Insert_35deg',outline,-1.6,1.0,carbide)
boolean(insert,cylinder('刀片中心通孔',1.12,-3,3));boolean(insert,cone('刀片沉孔',1.12,1.68,-.35,1.08));bevel(insert,.025,2)
# Fine machined perimeter land; reference does not specify a proprietary chip breaker.
# No invented proprietary chip-breaker geometry is added.
normals(insert)
shaft=cylinder('Screw_Shaft',1.0,-4.8,-.3,mat=screwmat);bevel(shaft,.045,3)
# Closed revolved head with a real socket and solid recessed floor.
N=96;vv=[]
for z,kind,radius in [(-.3,'circle',1.02),(1.06,'circle',1.52),(1.14,'circle',1.45),(1.14,'socket',0),(.59,'socket',0)]:
 for i in range(N):
  t=i*2*math.pi/N;r=radius if kind=='circle' else .62+.105*math.cos(6*t);vv.append((-1+r*math.cos(t),-5+r*math.sin(t),z))
ff=[]
for k in range(4):
 for i in range(N):j=(i+1)%N;ff.append((k*N+i,k*N+j,(k+1)*N+j,(k+1)*N+i))
vv.extend([(-1,-5,-.3),(-1,-5,.59)])
for i in range(N):
 j=(i+1)%N;ff.append((5*N,j,i));ff.append((5*N+1,4*N+i,4*N+j))
me=bpy.data.meshes.new('真实六瓣凹槽与沉头');me.from_pydata(vv,[],ff);me.update();head=bpy.data.objects.new('Screw_Head',me);bpy.context.collection.objects.link(head);head.data.materials.append(screwmat);normals(head);normals(shaft)
# Actual nose arc apex in local model coordinates, not the virtual sharp vertex.
C=Vector(centers[0]);virtual=Vector(vertices[0]);actual=C+(virtual-C).normalized()*R;tipxy=transform(actual);nominal_tip=[tipxy[0],tipxy[1],1.0];tip=list(min((v.co.copy() for v in insert.data.vertices),key=lambda q:(q-Vector(nominal_tip)).length))
for o in [body,seat,insert,shaft,head]:
 o['componentRole']={'Holder_Main':'holder','Insert_Seat':'seat','Carbide_Insert_35deg':'insert','Screw_Shaft':'fastener','Screw_Head':'fastener'}[o.name];o['dimensionVerification']='演示默认值，未核验制造商尺寸'
# Physical checks before glTF conversion. Contacts are deliberately not penetration.
from mathutils import Matrix
objects=[body,seat,insert,shaft,head]
def bvh(o):
 return BVHTree.FromPolygons([o.matrix_world@v.co for v in o.data.vertices],[list(f.vertices) for f in o.data.polygons],all_triangles=False)
qa={'noseRadius':R,'includedAngle':35,'contactPlanes':{'holderPocketFloor':-2.2,'seatBottom':-2.2,'seatTop':-1.6,'insertBottom':-1.6},'seatGap':0,'screwAxis':[-1,-5],'insertHoleAxis':[-1,-5],'screwShaftRadialClearance':.12,'components':{},'surfaceIntersections':{}}
for o in objects:
 bm=bmesh.new();bm.from_mesh(o.data);qa['components'][o.name]={'vertices':len(bm.verts),'faces':len(bm.faces),'nonManifoldEdges':sum(not e.is_manifold for e in bm.edges),'signedVolumeMm3':bm.calc_volume(signed=True),'finiteNormals':all(math.isfinite(c) for f in bm.faces for c in f.normal)};bm.free()
for A,B in [(body,insert),(body,head),(seat,head),(insert,head),(insert,shaft)]: qa['surfaceIntersections'][A.name+' / '+B.name]=len(bvh(A).overlap(bvh(B)))
qa['tipToMeshVertexDistanceMm']=min((v.co-Vector(tip)).length for v in insert.data.vertices)
qa['limitations']=['BVH 检查针对网格表面，不是认证CAD实体求交','刀座、背面与紧固孔内部为明确未核验的演示重建','座体与刀片及刀杆底面共面贴合为装配接触','螺纹、牌号、涂层、精确后角未核验；不模拟螺纹啮合','鼻圆在模型中以有限圆弧细分并含微小刃口倒角，基准按顶面圆弧设计点']
# Export meter-scale glTF; viewer converts to mm only for presentation.
root=bpy.data.objects.new('Tool35_Demo_mm_to_m',None);bpy.context.collection.objects.link(root);root.scale=(.001,)*3
for o in objects:o.parent=root
root['cuttingTipPosition_mm']=tip;root['toolId']='JJ-OD35-SAMPLE-001';root['referenceImage']='5-照片-5.jpg，第二排第四格';root['verifiedDimensions']=False
params={'schemaVersion':'1.0','toolId':'JJ-OD35-SAMPLE-001','toolName':'35°菱形外圆车刀 · 图片结构样板','toolType':'external-turning','holderWidth':10,'holderHeight':10,'holderLength':max(v.co.y for v in body.data.vertices)-min(v.co.y for v in body.data.vertices),'insertShape':'35° rhombus / V形，未确认ISO型号','insertIncludedAngle':35,'approachAngle':None,'noseRadius':R,'hand':'待确认','mountingOrientation':{'insertPlanRotation':-18,'rake':0,'status':'模型局部演示安装姿态，不是主偏角或实机安装值'},'cuttingTipPosition':tip,'nominalNoseArcApex':nominal_tip,'virtualSharpTipPosition':[*transform(vertices[0]),1.0],'modelSource':[{'file':'references/tooling/5-照片-5.jpg','region':'第二排第四格 / 35度菱形刀','dimensionsAvailable':False}],'verificationStatus':{'structure':'基于单张透视图可见结构重建，待用户复核','insertIncludedAngle':'图片标签与任务明确35°；模型解析构造35°','dimensions':'全部线性尺寸为演示默认值，非产品尺寸','approachAngle':'待确认','hiddenGeometry':'刀座底部、背面、沉孔与螺丝内部为演示重建'},'units':'mm','additionalDemoDimensions':{'rearShankDatumLength':65,'insertVirtualLongDiagonal':20,'insertVirtualShortDiagonal':2*b,'insertThickness':2.6,'seatThickness':.6,'centerHoleDiameter':2.24,'screwDrive':'演示六瓣凹槽，真实规格待确认'},'unconfirmed':['制造商与准确型号','刀杆宽高长度','刀片实际长短对角线、厚度与标准代号','实际鼻圆与刃口处理','主偏角、手向与实机安装方向','刀座背面、底部、内孔、后角及支承方式','螺丝规格、驱动型式、螺纹与锁紧方式','材质牌号、涂层与切屑槽']}
ROOT.joinpath('models').mkdir(exist_ok=True)
suffix=f'{R:.1f}';bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'models'/f'tool35-r{suffix}.blend'));bpy.ops.export_scene.gltf(filepath=str(ROOT/'models'/f'tool35-r{suffix}.glb'),export_format='GLB',export_extras=True,export_yup=True)
(ROOT/'models'/f'tool35-r{suffix}.json').write_text(json.dumps(params,ensure_ascii=False,indent=2))
(ROOT/'models'/f'quality-r{suffix}.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2))
print('MODEL_QA',json.dumps(qa,ensure_ascii=False))
