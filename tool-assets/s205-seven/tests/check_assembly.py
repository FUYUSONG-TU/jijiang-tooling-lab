"""Additional finite assembly check: reject vertices strictly inside another closed component.
Shared interface points within 0.002mm count as contact. Does not prove complete CAD boolean disjointness.
"""
import bpy,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1];out={}
D=Vector((.673,.417,.611)).normalized()
def parity(tree,p,direction):
 hits=0;start=p.copy()
 for i in range(50):
  pos,n,index,distance=tree.ray_cast(start,direction)
  if pos is None:return hits%2==1
  hits+=1;start=pos+direction*.001
 return False

def inside(tree,p):
 nearest=tree.find_nearest(p)
 if nearest[0] is None or nearest[3]<.002:return False
 directions=[D,Vector((.241,.893,.381)).normalized(),Vector((-.591,.271,.759)).normalized()]
 return sum(parity(tree,p,d)for d in directions)>=2
for file in sorted((R/'sources').glob('*.blend')):
 bpy.ops.wm.open_mainfile(filepath=str(file));bpy.context.view_layer.update();objects=[o for o in bpy.context.scene.objects if o.type=='MESH'];trees={o.name:BVHTree.FromPolygons([o.matrix_world@v.co for v in o.data.vertices],[list(f.vertices)for f in o.data.polygons])for o in objects};pairs=[]
 for i,a in enumerate(objects):
  for b in objects[i+1:]:
   hits=[]
   for source,target in [(a,b),(b,a)]:
    for v in source.data.vertices:
     q=source.matrix_world@v.co
     if inside(trees[target.name],q):hits.append({'source':source.name,'target':target.name,'point':list(q)})
   if hits:pairs.append({'a':a.name,'b':b.name,'strictInsideVertices':len(hits),'examples':hits[:3]})
 out[file.stem]=pairs
(R/'reports/assembly-check.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in out.items()if v},ensure_ascii=False))
