"""Independent stdlib GLB2 decoder: compare exported geometry with canonical mm metadata."""
import json,struct,math,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
META=json.loads((ROOT/'metadata/tool.json').read_text());results=[]
I=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]
def mul(a,b):return [sum(a[k*4+r]*b[c*4+k] for k in range(4)) for c in range(4) for r in range(4)]
def trs(n):
 if 'matrix'in n:return n['matrix']
 x,y,z,w=n.get('rotation',[0,0,0,1]);s=n.get('scale',[1,1,1]);t=n.get('translation',[0,0,0]);a=[1-2*y*y-2*z*z,2*x*y+2*w*z,2*x*z-2*w*y,0,2*x*y-2*w*z,1-2*x*x-2*z*z,2*y*z+2*w*x,0,2*x*z+2*w*y,2*y*z-2*w*x,1-2*x*x-2*y*y,0,*t,1]
 for c in range(3):
  for r in range(3):a[c*4+r]*=s[c]
 return a
def point(a,v):return [sum(a[k*4+r]*v[k] for k in range(3))+a[12+r] for r in range(3)]
def dist(a,b):return math.dist(a,b)
def bounds(pts):return {'min':[min(p[k]for p in pts)for k in range(3)],'max':[max(p[k]for p in pts)for k in range(3)]}
def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
for key,v in META['noseRadiusVariants'].items():
 path=ROOT/v['modelPath'];data=path.read_bytes();assert data[:4]==b'glTF'and struct.unpack_from('<I',data,4)[0]==2;assert struct.unpack_from('<I',data,8)[0]==len(data);offset=12;chunks={}
 while offset<len(data):
  size,kind=struct.unpack_from('<II',data,offset);chunks[kind]=data[offset+8:offset+8+size];offset+=8+size
 doc=json.loads(chunks[0x4E4F534A]);bin=chunks[0x004E4942];assert len(data)==v['bytes'];assert hashlib.sha256(data).hexdigest()==v['sha256']
 def accessor(i):
  a=doc['accessors'][i];view=doc['bufferViews'][a['bufferView']];fmt,size={5126:('f',4),5125:('I',4),5123:('H',2),5121:('B',1)}[a['componentType']];count={'VEC3':3,'VEC2':2,'VEC4':4,'SCALAR':1}[a['type']];stride=view.get('byteStride',count*size);start=view.get('byteOffset',0)+a.get('byteOffset',0);return [struct.unpack_from('<'+fmt*count,bin,start+k*stride) for k in range(a['count'])]
 allpts=[];components={};triangles=0;degenerate=0;min_normal=2;max_normal=0
 def walk(i,parent):
  global triangles,degenerate,min_normal,max_normal
  node=doc['nodes'][i];matrix=mul(parent,trs(node))
  if 'mesh'in node:
   pts=[]
   for primitive in doc['meshes'][node['mesh']]['primitives']:
    assert primitive.get('mode',4)==4;positions=[point(matrix,p)for p in accessor(primitive['attributes']['POSITION'])];positions=[[p[0]*1000,-p[2]*1000,p[1]*1000]for p in positions];assert all(math.isfinite(x)for p in positions for x in p)
    normals=accessor(primitive['attributes']['NORMAL']);lengths=[math.sqrt(sum(x*x for x in n)) for n in normals];min_normal=min(min_normal,min(lengths));max_normal=max(max_normal,max(lengths));assert all(abs(n-1)<.001 for n in lengths)
    indices=[x[0]for x in accessor(primitive['indices'])] if'indices'in primitive else list(range(len(positions)));assert len(indices)%3==0;assert max(indices)<len(positions);triangles+=len(indices)//3
    for k in range(0,len(indices),3):
     a,b,c=[positions[j]for j in indices[k:k+3]];area=math.sqrt(sum(x*x for x in cross([b[j]-a[j]for j in range(3)],[c[j]-a[j]for j in range(3)])))/2
     if area<1e-10:degenerate+=1
    pts+=positions
   components[node['name']]=pts;allpts.extend(pts)
  for child in node.get('children',[]):walk(child,matrix)
 for i in doc['scenes'][doc.get('scene',0)]['nodes']:walk(i,I)
 assert set(components)==set(v['components']);B=bounds(allpts);bbox_error=max(abs(B[k][j]-v['boundingBox'][k][j])for k in ['min','max']for j in range(3));assert bbox_error<.0002
 for name,pts in components.items():
  b=bounds(pts);assert max(abs(b[k][j]-v['components'][name]['boundingBox'][k][j])for k in ['min','max']for j in range(3))<.0002
 tip_error=min(dist(p,v['cuttingTipPosition'])for p in components['Carbide_Insert_35deg']);assert tip_error<.0002
 # Outer side-wall vertices retain the design circle despite the small top-edge chamfer.
 c=v['noseArcCenter'];radius=v['noseRadius'];arc=[p for p in components['Carbide_Insert_35deg'] if abs(math.hypot(p[0]-c[0],p[1]-c[1])-radius)<.00002 and p[1]<c[1]]
 assert len(arc)>=15,('insufficient measured arc vertices',key,len(arc));arc_error=max(abs(math.hypot(p[0]-c[0],p[1]-c[1])-radius)for p in arc)
 # Fit long straight flanks from exported mid-height contour; acute-angle cannot be checked by metadata alone.
 contour=components['Carbide_Insert_35deg'];theta=math.radians(-18);bx,by=-1,-70
 local=[((p[0]-bx)*math.cos(theta)+(p[1]-by)*math.sin(theta),-(p[0]-bx)*math.sin(theta)+(p[1]-by)*math.cos(theta))for p in contour if abs(p[2]-3.425)<.0002 or abs(p[2]-5.975)<.0002]
 slopes=[]
 for sign in [-1,1]:
  flank=list(set((round(x,6),round(y,6))for x,y in local if y<1 and sign*x>0 and abs(abs(x)-(y+10)*math.tan(math.radians(17.5)))<.0001))

  assert len(flank)>=2,(key,'missing flank',sign)
  xx=[p[0]for p in flank];yy=[p[1]for p in flank];xa=sum(xx)/len(xx);ya=sum(yy)/len(yy);slope=sum((x-xa)*(y-ya)for x,y in flank)/sum((y-ya)**2 for y in yy);slopes.append(slope)
 angle=abs(math.degrees(math.atan(slopes[1])-math.atan(slopes[0])));assert abs(angle-35)<.002,(key,angle)
 assert degenerate==0,(key,'degenerate triangles',degenerate)
 for q in v['sourceQA']['meshes'].values():assert q['nonManifoldEdges']==0 and q['positiveVolume']and q['finiteNormals']
 assert all(n==0 for n in v['sourceQA']['surfaceIntersectionCounts'].values())
 results.append({'variant':key,'bytes':len(data),'meshCount':len(components),'materialCount':len(doc.get('materials',[])),'textureCount':len(doc.get('textures',[])),'triangles':triangles,'bboxMaxErrorMm':bbox_error,'tipVertexErrorMm':tip_error,'measuredIncludedAngleDegrees':angle,'measuredNoseRadiusMm':radius,'arcVertices':len(arc),'arcMaxErrorMm':arc_error,'degenerateTriangles':degenerate})
assert len({tuple(v['cuttingTipPosition'])for v in META['noseRadiusVariants'].values()})==3
assert len({tuple(v['noseArcCenter'])for v in META['noseRadiusVariants'].values()})==3
assert META['professionalToolCount']==1
report={'passed':True,'variantCount':3,'professionalToolCount':1,'results':results,'totalModelBytes':sum(r['bytes']for r in results),'limits':'离散网格/指定表面检查，不是CAD实体安全或厂家尺寸认证'}
(ROOT/'reports/assets.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))
