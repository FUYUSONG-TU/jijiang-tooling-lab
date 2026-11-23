import bpy,json,bmesh
from pathlib import Path
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1];out={}
for f in sorted((R/'sources').glob('*.blend')):
 bpy.ops.wm.open_mainfile(filepath=str(f));assert abs(bpy.context.scene.unit_settings.scale_length-.001)<1e-8;assert bpy.context.scene.unit_settings.length_unit=='MILLIMETERS';rows={}
 for o in bpy.context.scene.objects:
  if o.type!='MESH':continue
  o.data.calc_loop_triangles();tri=[tuple(t.vertices)for t in o.data.loop_triangles];verts=[v.co.copy()for v in o.data.vertices];tree=BVHTree.FromPolygons(verts,tri,all_triangles=True);hits=[]
  for a,b in tree.overlap(tree):
   if a>=b or set(tri[a])&set(tri[b]):continue
   hits.append([a,b])
  rows[o.name]={'selfIntersectionCandidates':len(hits),'examples':hits[:8]}
 out[f.stem]=rows
(R/'reports/self-intersections.json').write_text(json.dumps(out,indent=2));print('SELF_QA',json.dumps(out))
