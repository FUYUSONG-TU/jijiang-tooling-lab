import json,struct,math,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];catalog=json.loads((R/'catalog.json').read_text());assert len(catalog['tools'])==7
I=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]
def mul(a,b):return[sum(a[k*4+r]*b[c*4+k]for k in range(4))for c in range(4)for r in range(4)]
def transform(n):
 if'matrix'in n:return n['matrix']
 x,y,z,w=n.get('rotation',[0,0,0,1]);s=n.get('scale',[1,1,1]);t=n.get('translation',[0,0,0]);a=[1-2*y*y-2*z*z,2*x*y+2*w*z,2*x*z-2*w*y,0,2*x*y-2*w*z,1-2*x*x-2*z*z,2*y*z+2*w*x,0,2*x*z+2*w*y,2*y*z-2*w*x,1-2*x*x-2*y*y,0,*t,1]
 for c in range(3):
  for r in range(3):a[c*4+r]*=s[c]
 return a
def point(a,v):return[sum(a[k*4+r]*v[k]for k in range(3))+a[12+r]for r in range(3)]
def sub(a,b):return[a[i]-b[i]for i in range(3)]
def add(a,b):return[a[i]+b[i]for i in range(3)]
def scale(a,s):return[x*s for x in a]
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
def closest(p,a,b,c):
 ab,ac,ap=sub(b,a),sub(c,a),sub(p,a);d1,d2=dot(ab,ap),dot(ac,ap)
 if d1<=0 and d2<=0:return a
 bp=sub(p,b);d3,d4=dot(ab,bp),dot(ac,bp)
 if d3>=0 and d4<=d3:return b
 vc=d1*d4-d3*d2
 if vc<=0 and d1>=0 and d3<=0:return add(a,scale(ab,d1/(d1-d3)))
 cp=sub(p,c);d5,d6=dot(ab,cp),dot(ac,cp)
 if d6>=0 and d5<=d6:return c
 vb=d5*d2-d1*d6
 if vb<=0 and d2>=0 and d6<=0:return add(a,scale(ac,d2/(d2-d6)))
 va=d3*d6-d5*d4
 if va<=0 and d4>=d3 and d5>=d6:return add(b,scale(sub(c,b),(d4-d3)/((d4-d3)+(d5-d6))))
 denominator=va+vb+vc
 if abs(denominator)<1e-20:return a
 return add(a,add(scale(ab,vb/denominator),scale(ac,vc/denominator)))
results=[]
for entry in catalog['tools']:
 m=json.loads((R/entry['metadataPath']).read_text());raw=(R/m['modelPath']).read_bytes();assert raw[:4]==b'glTF'and struct.unpack_from('<II',raw,4)==(2,len(raw));assert len(raw)==m['bytes'];assert hashlib.sha256(raw).hexdigest()==m['sha256'];off=12;chunks={}
 while off<len(raw):
  size,kind=struct.unpack_from('<II',raw,off);chunks[kind]=raw[off+8:off+8+size];off+=8+size
 doc=json.loads(chunks[0x4E4F534A]);bin=chunks[0x004E4942]
 def acc(i):
  a=doc['accessors'][i];b=doc['bufferViews'][a['bufferView']];fmt,size={5126:('f',4),5125:('I',4),5123:('H',2)}[a['componentType']];n={'VEC3':3,'VEC2':2,'SCALAR':1,'VEC4':4}[a['type']];start=b.get('byteOffset',0)+a.get('byteOffset',0);stride=b.get('byteStride',size*n);return[struct.unpack_from('<'+fmt*n,bin,start+k*stride)for k in range(a['count'])]
 points=[];count=0;degenerate=0;tipError=1e9;mountError=1e9;parts=set();primitives=0
 def walk(i,parent):
  global count,degenerate,tipError,mountError,primitives
  n=doc['nodes'][i];matrix=mul(parent,transform(n))
  if'mesh'in n:
   parts.add(n['name']);assert n.get('extras',{}).get('componentRole')
   for pr in doc['meshes'][n['mesh']]['primitives']:
    primitives+=1;assert pr.get('mode',4)==4;ps=[point(matrix,p)for p in acc(pr['attributes']['POSITION'])];ps=[[p[0]*1000,-p[2]*1000,p[1]*1000]for p in ps];assert all(math.isfinite(v)for p in ps for v in p);points.extend(ps)
    for norm in acc(pr['attributes']['NORMAL']):assert abs(math.sqrt(dot(norm,norm))-1)<.001
    idx=[v[0]for v in acc(pr['indices'])];assert len(idx)%3==0 and max(idx)<len(ps);count+=len(idx)//3
    for k in range(0,len(idx),3):
     a,b,c=[ps[j]for j in idx[k:k+3]];normal=cross(sub(b,a),sub(c,a));area=math.sqrt(dot(normal,normal))/2
     if area<1e-10:degenerate+=1;continue
     tipError=min(tipError,math.dist(m['cuttingReferencePoint'],closest(m['cuttingReferencePoint'],a,b,c)));mountError=min(mountError,math.dist([0,0,0],closest([0,0,0],a,b,c)))
  for child in n.get('children',[]):walk(child,matrix)
 for i in doc['scenes'][doc.get('scene',0)]['nodes']:walk(i,I)
 B={'min':[min(p[i]for p in points)for i in range(3)],'max':[max(p[i]for p in points)for i in range(3)]};err=max(abs(B[k][i]-m['boundingBox'][k][i])for k in B for i in range(3));assert err<.0002,(entry['toolType'],err);assert tipError<.0002,(entry['toolType'],tipError);assert mountError<.0002,(entry['toolType'],mountError);assert degenerate==0,(entry['toolType'],degenerate);assert count==m['triangleCount']and count<12000;assert set(m['components'])==parts
 for v in m['selfInspection']['meshes'].values():assert v['nonManifoldEdges']==0 and v['signedVolumeMm3']>0 and v['finiteNormals']
 for c in m['selfInspection']['holderInsertSurfaceChecks']:assert c['surfaceOverlaps']==0
 results.append({'toolType':entry['toolType'],'bytes':len(raw),'triangles':count,'parts':len(parts),'drawPrimitives':primitives,'materials':len(doc.get('materials',[])),'textures':len(doc.get('textures',[])),'bboxMaxErrorMm':err,'referenceSurfaceErrorMm':tipError,'mountSurfaceErrorMm':mountError,'degenerateTriangles':degenerate})
selfQa=json.loads((R/'reports/self-intersections.json').read_text());assert all(v['selfIntersectionCandidates']==0 for q in selfQa.values()for v in q.values())
assembly=json.loads((R/'reports/assembly-check.json').read_text());assert not any(assembly.values()),'装配顶点穿入候选需要复核'
out={'passed':True,'loadedAssetCount':len(results),'totalGlbBytes':sum(r['bytes']for r in results),'results':results,'selfIntersectionCandidates':0,'limits':'数字几何检查，不代表厂家尺寸认证或所有夹紧接触/实体体积安全'};(R/'reports/glb-validation.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print(json.dumps(out,ensure_ascii=False,indent=2))
