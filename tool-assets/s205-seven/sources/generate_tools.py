"""Blender4.3 reproducible seven teaching tools; no manufacturer-specific dimensional claims.
All design coordinates mm, rear mounting origin (0,0,0), forward -Y, top +Z.
Run blender -b --python tool-assets/s205-seven/sources/generate_tools.py
"""
import bpy,bmesh,math,json,hashlib
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1]
for d in ['models','metadata','reports']:(R/d).mkdir(exist_ok=True)
records=[];objects=[]
def active(o):
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o

def material(name,color,metal=.8,rough=.27):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Metallic'].default_value=metal;bs.inputs['Roughness'].default_value=rough;return m

def start():
 global objects,steel,dark,gold,carbide,polish
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);objects=[];bpy.context.scene.unit_settings.system='METRIC';bpy.context.scene.unit_settings.scale_length=.001;bpy.context.scene.unit_settings.length_unit='MILLIMETERS'
 steel=material('磨削钢',(.37,.44,.51));dark=material('夹紧钢/黑化',(.055,.08,.1),.76,.32);gold=material('硬质合金刀片/演示涂层',(.73,.43,.12),.78,.23);carbide=material('整体硬质合金/演示涂层',(.12,.20,.24),.85,.23);polish=material('磨削刃带',(.65,.71,.76),.85,.2)

def tag(o,name,role,mat):
 o.name=name;o.data.materials.append(mat);o['componentRole']=role;o['verifiedManufacturerDimensions']=False;objects.append(o);return o

def fix(o):
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();o.data.update()

def bevel(o,w=.12,n=3):
 active(o);m=o.modifiers.new('实际边缘倒角','BEVEL');m.width=w;m.segments=n;bpy.ops.object.modifier_apply(modifier=m.name)

def weighted(o):
 active(o);m=o.modifiers.new('加权法线','WEIGHTED_NORMAL');m.keep_sharp=True;bpy.ops.object.modifier_apply(modifier=m.name)

def poly(name,pts,z0,z1,mat,role='holder'):
 n=len(pts);vs=[(x,y,z)for z in [z0,z1]for x,y in pts];fs=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n)for i in range(n)];me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);tag(o,name,role,mat);fix(o);return o

def box(name,size,loc,mat,role='holder',edge=.12):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.dimensions=size;active(o);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);tag(o,name,role,mat)
 if edge:bevel(o,edge)
 return o

def cyl(name,r,a,b,mat,role='toolShank',axis='Y',center=(0,0,0),verts=48):
 c=list(center);k={'X':0,'Y':1,'Z':2}[axis];c[k]=(a+b)/2;bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=b-a,location=c);o=bpy.context.object
 if axis=='Y':o.rotation_euler.x=math.pi/2
 if axis=='X':o.rotation_euler.y=math.pi/2
 tag(o,name,role,mat);
 for f in o.data.polygons:
  if len(f.vertices)==4:f.use_smooth=True
 return o

def diff(o,c):
 # Cutters are real geometry and removed after exact boolean evaluation.
 active(o);m=o.modifiers.new('实体开孔/刀座','BOOLEAN');m.operation='DIFFERENCE';m.solver='EXACT';m.object=c;bpy.ops.object.modifier_apply(modifier=m.name)
 if c in objects:objects.remove(c)
 bpy.data.objects.remove(c,do_unlink=True)

def socket_screw(name,axis='Z',center=(0,-64,0),shaft=(4,8.5),radius=.95,head=1.45):
 s=cyl(name+'_Shaft',radius,*shaft,dark,'fastener',axis,center,32)
 # Built as closed rings: cone seat, head crown, genuine hex socket and recessed floor.
 n=48;vs=[];h0=shaft[1];heightScale=head/1.45;rings=[(h0,'circle',head*.8),(h0+.45*heightScale,'circle',head),(h0+1.3*heightScale,'circle',head),(h0+1.35*heightScale,'hex',head*.48),(h0+.65*heightScale,'hex',head*.48)]
 def coord(u,v,t):
  return (u+center[0],v+center[1],t)if axis=='Z'else(t,u+center[1],v+center[2])
 for z,kind,r in rings:
  for i in range(n):
   a=i*2*math.pi/n;rr=r if kind=='circle'else r*math.cos(math.pi/6)/math.cos((a+math.pi/6)%(math.pi/3)-math.pi/6);vs.append(coord(rr*math.cos(a),rr*math.sin(a),z))
 fs=[]
 for k in range(4):
  for i in range(n):j=(i+1)%n;fs.append((k*n+i,k*n+j,(k+1)*n+j,(k+1)*n+i))
 vs.extend([coord(0,0,h0),coord(0,0,h0+.65*heightScale)])
 for i in range(n):j=(i+1)%n;fs.extend([(5*n,j,i),(5*n+1,4*n+i,4*n+j)])
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(name+'_Head',me);bpy.context.collection.objects.link(o);tag(o,o.name,'fastener',dark);fix(o);return [s,o]

def nearest(o,nominal):
 bpy.context.view_layer.update();tree=BVHTree.FromPolygons([o.matrix_world@v.co for v in o.data.vertices],[list(p.vertices)for p in o.data.polygons]);point,normal,idx,distance=tree.find_nearest(Vector(nominal));return list(point)

def rounded(points,r=.1):
 out=[]
 for i,p in enumerate(points):
  p=Vector(p);u=(Vector(points[i-1])-p).normalized();v=(Vector(points[(i+1)%len(points)])-p).normalized();alpha=math.acos(u.dot(v));c=p+(u+v).normalized()*r/math.sin(alpha/2);a=p+u*r/math.tan(alpha/2);b=p+v*r/math.tan(alpha/2);a1=math.atan2(a.y-c.y,a.x-c.x);a2=math.atan2(b.y-c.y,b.x-c.x)
  while a2<a1:a2+=2*math.pi
  if a2-a1>math.pi:a2-=2*math.pi
  for j in range(9):t=a1+(a2-a1)*j/8;out.append((c.x+r*math.cos(t),c.y+r*math.sin(t)))
 return out

def external_groove():
 start();body=poly('Groove_Holder',[(-5,0),(-5,-60),(-2,-74),(2,-74),(5,-60),(5,0)],-5,5,steel);bevel(body,.18)
 diff(body,box('座腔',(2.25,9,4),(0,-74,4.5),dark,edge=0))
 diff(body,cyl('夹紧盲孔',1.08,1.5,9,dark,axis='Z',center=(0,-64,0)))
 seat=box('Groove_Seat',(2,4,.5),(0,-72,2.75),dark,'seat',.035)
 insert=poly('Groove_Carbide_Insert',[(-1,-78),(1,-78),(1,-70),(-1,-70)],3,5.5,gold,'insert');
 for v in insert.data.vertices:
  if v.co.z<3.1:
   v.co.x*=.82
   if v.co.y< -77:v.co.y+=.35
 fix(insert);bevel(insert,.035,2);diff(insert,cyl('切槽断屑凹槽',.55,-77.45,-70.3,dark,axis='Y',center=(0,0,5.85)))
 # Y/Z profiled clamp with lower nose at insert top; not a rectangular placeholder.
 pts=[(-71,5.5),(-69,5.5),(-69,5),(-61,5),(-61,8.5),(-68,8.5),(-71,7)]
 clamp=poly('Groove_Top_Clamp',pts,-2,2,dark,'clamp')
 # poly x/y becomes original Y/Z; original z becomes physical X.
 for v in clamp.data.vertices:x,y,z=v.co;v.co=(z,x,y)
 fix(clamp);diff(clamp,cyl('夹紧通孔',1.12,4,10,dark,axis='Z',center=(0,-64,0)));bevel(clamp,.06,2)
 socket_screw('Groove_Clamp_Screw',center=(0,-64,0),shaft=(1.7,8.5))
 return finish('external-grooving','外圆切槽刀',['external-grooving'],insert,(0,-78,5.5),'gang-od',{'cuttingWidth':2,'insertThickness':2.5,'maximumIllustrativeOverhang':4,'cuttingEdge':'2mm前刃，圆角和后角为教学形体'},'第5张图第二排第三格外圆切槽刀及第3张图G/H类工位；不是产品尺寸复刻')

def parting():
 start();holder=box('Parting_Holder',(10,60,10),(0,-30,0),steel,edge=.18);diff(holder,box('刀板槽',(1.8,18,12),(.1,-58,0),dark,edge=0))
 blade=poly('Parting_Blade',[(-54,-5),(-81,-5),(-83,2.6),(-83,5),(-54,5)],-.8,.8,steel,'bladeCarrier')
 for v in blade.data.vertices:x,y,z=v.co;v.co=(z,x,y)
 fix(blade);bevel(blade,.06,2)
 diff(blade,box('刀片座腔',(1.9,5.5,3),(0,-81.5,4),dark,edge=0))
 insert=poly('Parting_Carbide_Insert',[(-.75,-85),(.75,-85),(.68,-79),(-.68,-79)],3,5.5,gold,'insert');
 for v in insert.data.vertices:
  if v.co.z<3.1:
   v.co.x*=.84
   if v.co.y< -84:v.co.y+=.35
 fix(insert);bevel(insert,.025,2);diff(insert,cyl('切断刀断屑槽',.42,-84.4,-79.2,dark,axis='Y',center=(0,0,5.8)))
 for yy in [-54,-59]:
  diff(holder,cyl('侧向螺孔',.95,.78,5.5,dark,axis='X',center=(0,yy,0)))
  socket_screw('Parting_Side_'+str(-yy),axis='X',center=(0,yy,0),shaft=(.8,5),radius=.85,head=1.25)
 return finish('parting-off','切断刀',['parting-off'],insert,(0,-85,5.5),'gang-od',{'bladeThickness':1.6,'cuttingWidth':1.5,'insertThickness':2.5,'clamp':'侧压紧固，螺纹未建模'},'第3张图切断H类工位；切断刀板与压紧细节为通用教学结构')

def threading():
 start();body=poly('Thread_Holder',[(-5,0),(-5,-60),(-3.8,-72),(0,-74.8),(4.5,-70),(5,-60),(5,0)],-5,5,steel);bevel(body,.18)
 tri=[(0,-76),(4,-69.0718),(-4,-69.0718)];outline=rounded(tri,.12)
 diff(body,poly('螺纹刀座',rounded([(x*1.035,-71.4+(y+71.4)*1.035)for x,y in tri],.16),2.3,8,dark))
 seat=poly('Thread_Seat',rounded([(x*.94,-71.4+(y+71.4)*.94)for x,y in tri],.1),2.3,2.9,dark,'seat')
 insert=poly('Thread_60deg_Insert',outline,2.9,5.6,gold,'insert');bevel(insert,.025,2)
 breaker=poly('通用三角断屑凹面',rounded([(x*.82,-71.4+(y+71.4)*.82)for x,y in tri],.1),5.28,6,dark);diff(breaker,cyl('保留中心支承岛',1.6,5,7,dark,axis='Z',center=(0,-71.3,0)));diff(insert,breaker)
 for o in [body,seat,insert]:diff(o,cyl('同轴孔',1.04,0,8,dark,axis='Z',center=(0,-71.3,0)))
 socket_screw('Thread_Insert_Screw',center=(0,-71.3,0),shaft=(.5,5.6),radius=.93,head=1.4)
 return finish('external-threading','外螺纹刀',['external-threading-60deg-partial-profile'],insert,(0,-76,5.6),'gang-od',{'insertIncludedAngle':60,'noseRadius':.12,'pitch':None,'profile':'60°局部牙型；未指定螺距/全牙型'},'第3张图螺纹J类工位和第5张图三角刀片构造；60°牙型为通用教学选择')

# True concave multi-start flutes: the material boundary itself twists, not raised decorative helices.
def groove_radius(phase):
 knots=[(0,1),(.08,1),(.17,.38),(.42,.37),(.78,.87),(1,1)]
 for (a,x),(b,y)in zip(knots,knots[1:]):
  if a<=phase<=b:return x+(y-x)*(phase-a)/(b-a)
 return 1

def fluted(name,profile,flutes,helix,material,length_steps=48,angular=48,endmill=False):
 # profile = [(forward distance, outer radius)], last radius may be zero apex.
 def radius_at(d):
  for (a,r),(b,s)in zip(profile,profile[1:]):
   if a<=d<=b:return r+(s-r)*(d-a)/(b-a)
  return profile[-1][1]
 start_d,end_d=profile[0][0],profile[-1][0];base_r=max(r for _,r in profile);ds=sorted(set([start_d+(end_d-start_d)*k/length_steps for k in range(length_steps+1)]+[d for d,_ in profile]));vs=[];rings=[];faces=[];face_materials=[]
 for d in ds:
  rr=radius_at(d)
  if rr<1e-7:rings.append([len(vs)]);vs.append((0,-d,0));continue
  ring=[];ramp=min(1,(d-start_d)/1.5)
  for j in range(angular):
   angle=2*math.pi*j/angular;phase=(j*flutes/angular)%1;rho=rr*(1-ramp*(1-groove_radius(phase)));twist=(d-start_d)/base_r*math.tan(math.radians(helix));t=angle+twist;advance=.65*(1-phase)*max(0,(d-(end_d-2))/2) if endmill and phase>.08 else 0
   ring.append(len(vs));vs.append((rho*math.cos(t),-d+advance,rho*math.sin(t)))
  rings.append(ring)
 for k,(a,b)in enumerate(zip(rings,rings[1:])):
  for j in range(angular):
   q=(j+1)%angular
   if len(b)==1:faces.append((a[j],a[q],b[0]))
   else:faces.append((a[j],a[q],b[q],b[j]))
   face_materials.append(1 if (j*flutes/angular)%1<.085 else 0)
 for ri,d in [(0,start_d),(-1,end_d)]:
  ring=rings[ri]
  if len(ring)==1:continue
  center=len(vs);vs.append((0,-d+(.45 if endmill and ri==-1 else 0),0))
  for j in range(angular):faces.append((center,ring[j],ring[(j+1)%angular]));face_materials.append(1)
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],faces);me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);tag(o,name,'cuttingBody',material);o.data.materials.append(polish);fix(o)
 for f,idx in zip(o.data.polygons,face_materials):f.material_index=idx
 # Smooth the actual curved flute walls; terminal grinds remain faceted.
 for f in o.data.polygons:
  if len(f.vertices)==4:f.use_smooth=True
 return o

def center_drill():
 start();shank=cyl('CenterDrill_Shank',3,-16,0,steel);bevel(shank,.08,2)
 d=20+2/math.tan(math.radians(30));L=d+3+1/math.tan(math.radians(59));body=fluted('CenterDrill_Pilot_And_60deg_Cone',[(16,3),(20,3),(d,1),(d+3,1),(L,0)],2,12,steel,42,48)
 return finish('center-drill','中心钻',['centering','pilot-hole'],body,(0,-L,0),'axial-static',{'bodyDiameter':6,'pilotDiameter':2,'centeringIncludedAngle':60,'pilotPointAngle':118,'flutes':2,'helixAngle':12},'第3张图K类轴向钻孔工位；中心钻刃型无特定厂家资料，采用通用组合中心钻教学形体')

def twist_drill():
 start();shank=cyl('TwistDrill_Shank',2,-22,0,steel);bevel(shank,.08,2);L=54+2/math.tan(math.radians(59));body=fluted('TwistDrill_2_Helical_Flutes',[(22,2),(54,2),(L,0)],2,30,steel,60,48)
 return finish('twist-drill','麻花钻',['axial-drilling'],body,(0,-L,0),'axial-static',{'diameter':4,'pointIncludedAngle':118,'helixAngle':30,'flutes':2,'web':'连续实体芯厚；横刃/后刀面为近似，非精密磨削模型'},'第3张图K类轴向钻孔和实拍钻头；尺寸/螺旋参数为通用教学值')

def boring():
 start();shank=cyl('BoringBar_Round_Shank',4,-43,0,steel,'holder');bevel(shank,.1,2);neck=cyl('BoringBar_Reduced_Neck',2.8,-65,-43,steel,'holder')
 # Ground flat and open pocket at the bar nose.
 diff(neck,box('前段磨削平面',(8,10,5),(0,-63,4.2),dark,edge=0))
 tri=[(3.7,-67.7),(3.4,-61.8),(-1.6,-64.8)];insert=poly('BoringBar_Carbide_Insert',rounded(tri,.1),1.3,2.7,gold,'insert');bevel(insert,.02,2)
 pad=poly('BoringBar_Seat',[(2.8,-65),(-1.5,-65),(-1.5,-62),(2.8,-62)],.85,1.3,dark,'seat')
 diff(neck,box('内孔刀片座',(5.2,4.2,4),(1,-63,2.85),dark,edge=0))
 for o in [neck,pad,insert]:diff(o,cyl('镗刀紧固孔',.72,-1,5,dark,axis='Z',center=(1.5,-64,0)))
 socket_screw('BoringBar_Insert_Screw',center=(1.5,-64,0),shaft=(-1,2.7),radius=.63,head=.95)
 return finish('internal-boring','内孔镗杆',['internal-boring','internal-facing'],insert,(3.7,-67.7,2.7),'axial-boring',{'shankDiameter':8,'neckDiameter':5.6,'insert':'小型可转位刀片，非MTR型号复刻','radialCuttingOffset':'以元数据实际切削参考点为准'},'第1张内孔刀具图用于圆柄/缩颈/前刃结构参考，第3张F类内径加工；可转位座体为教学重建')

def end_mill():
 start();shank=cyl('EndMill_Solid_Carbide_Shank',3,-24,0,carbide);bevel(shank,.08,2);body=fluted('EndMill_4_Flutes_End_Gashes',[(24,3),(45,3)],4,35,carbide,48,64,True)
 # A real front cutting corner on one helical tooth; not the empty axis-intercept.
 front=[v.co.copy()for v in body.data.vertices if v.co.y<-44.99];corner=max(front,key=lambda v:v.x)
 return finish('solid-carbide-endmill','整体硬质合金立铣刀',['driven-end-milling','driven-side-milling'],body,corner,'optional-driven',{'diameter':6,'flutes':4,'helixAngle':35,'endGeometry':'四刃端部排屑/后隙近似；未认证中心切削能力','centerCuttingVerified':False},'现有参考图不能确认S205动力头选配；采用通用四刃整体硬质合金形体，仅允许条件动力工位')

def bbox(pts):
 lo=[min(p[k]for p in pts)for k in range(3)];hi=[max(p[k]for p in pts)for k in range(3)];return {'min':lo,'max':hi,'size':[hi[k]-lo[k]for k in range(3)]}

def finish(id,name,ops,cutting,nominal,station,params,reference):
 bpy.context.view_layer.update();tip=nearest(cutting,nominal);pts=[];qa={};component_boxes={}
 for o in objects:
  active(o);bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);fix(o)
  points=[v.co.copy()for v in o.data.vertices];pts+=points;component_boxes[o.name]={'role':o['componentRole'],'boundingBox':bbox(points)}
  bm=bmesh.new();bm.from_mesh(o.data);qa[o.name]={'nonManifoldEdges':sum(not e.is_manifold for e in bm.edges),'signedVolumeMm3':bm.calc_volume(signed=True),'finiteNormals':all(math.isfinite(x)for f in bm.faces for x in f.normal),'vertices':len(bm.verts)};bm.free()
 # These exclude intentional press/contact interfaces and shared end faces.
 pairs=[]
 for a in objects:
  for b in objects:
   if a.name>=b.name:continue
   if set([a['componentRole'],b['componentRole']])==set(['holder','insert']):
    ta=BVHTree.FromPolygons([v.co for v in a.data.vertices],[list(f.vertices)for f in a.data.polygons]);tb=BVHTree.FromPolygons([v.co for v in b.data.vertices],[list(f.vertices)for f in b.data.polygons]);pairs.append({'a':a.name,'b':b.name,'surfaceOverlaps':len(ta.overlap(tb))})
 meta={'schemaVersion':'3.0','modelVersion':'1.0.0','toolId':'JJ-'+id.upper(),'toolName':name,'toolType':id,'supportedOperations':ops,'geometryUnits':{'metadata':'mm/Z-up','glb':'m/Y-up','loaderOutput':'mm/Z-up'},'mountingOrigin':[0,0,0],'cuttingReferencePoint':tip,'cuttingReferenceDefinition':'实际网格上选定的前刃/切削角基准，不等于模型中心；圆柱工具轴线另行记录','localCoordinateAxes':{'handedness':'right','X':'横向宽度','Y':'朝向安装后端，切削端在负Y','Z':'刀片顶面/径向截面竖向'},'axisDirection':[0,-1,0],'axisOrigin':[0,0,0],'axialGaugePoint':[0,min(v.y for v in pts),0],'boundingBox':bbox(pts),'overallDimensions':dict(zip(['widthX','lengthY','heightZ'],bbox(pts)['size'])),'parameters':params,'components':component_boxes,'compatibleStationTypes':[station],'stationConfigurationVerified':False,'verificationStatus':{'dimensions':'全部为明确教学默认值，不是厂家尺寸或图片透视测量','structure':'参考可见结构+通用参数化教学重建，隐藏内部与螺纹非精确产品复刻','manufacturer':None,'nativeWechat':'未原生微信真机测试'},'referenceEvidence':reference,'sourceFile':'sources/generate_tools.py','modelPath':'models/'+id+'.glb','selfInspection':{'meshes':qa,'holderInsertSurfaceChecks':pairs,'contactPolicy':'座面、螺丝座及部件端面有意接触不视为错误穿透；非完整CAD实体认证'}}
 # Material/part split retained. Apply metre conversion to vertex coordinates only.
 bpy.ops.wm.save_as_mainfile(filepath=str(R/'sources'/(id+'.blend')))
 bpy.context.scene.unit_settings.scale_length=1;bpy.context.scene.unit_settings.length_unit='METERS'
 for o in objects:
  for v in o.data.vertices:v.co*=.001
  o.data.update()
  o['toolId']=meta['toolId'];o['modelVersion']='1.0.0'
 bpy.ops.export_scene.gltf(filepath=str(R/meta['modelPath']),export_format='GLB',export_yup=True,export_extras=True,export_cameras=False,export_lights=False)
 data=(R/meta['modelPath']).read_bytes();gltf=json.loads(data[20:20+int.from_bytes(data[12:16],'little')]);meta['triangleCount']=sum(gltf['accessors'][p['indices']]['count']//3 for mesh in gltf['meshes'] for p in mesh['primitives']);meta['meshCount']=len(gltf['meshes']);meta['drawPrimitiveCount']=sum(len(mesh['primitives']) for mesh in gltf['meshes']);meta['materialCount']=len(gltf.get('materials',[]));meta['textureCount']=len(gltf.get('textures',[]));meta['mountingInterface']={'type':'square-shank' if station=='gang-od' else 'round-shank','squareWidth':10 if station=='gang-od' else None,'shankDiameter':None if station=='gang-od' else params.get('shankDiameter',params.get('bodyDiameter',params.get('diameter'))),'gripRegionLocalY':[-12,0]};meta['bytes']=len(data);meta['sha256']=hashlib.sha256(data).hexdigest();(R/'metadata'/(id+'.json')).write_text(json.dumps(meta,ensure_ascii=False,indent=2));records.append(meta)
 print('TOOL_FINISHED',id,len(data),[(k,v['nonManifoldEdges'])for k,v in qa.items()])
 return meta

for build in [external_groove,parting,threading,center_drill,twist_drill,boring,end_mill]:build()
(R/'catalog.json').write_text(json.dumps({'schemaVersion':'3.0','modelVersion':'1.0.0','toolCount':7,'tools':[{'toolId':m['toolId'],'toolType':m['toolType'],'toolName':m['toolName'],'metadataPath':'metadata/'+m['toolType']+'.json','modelPath':m['modelPath']}for m in records]},ensure_ascii=False,indent=2))
