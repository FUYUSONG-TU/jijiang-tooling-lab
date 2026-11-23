import * as T from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
export const assetBase=new URL('../',import.meta.url);
export const conversion=new T.Matrix4().makeRotationX(Math.PI/2).scale(new T.Vector3(1000,1000,1000));
export function createToolLibrary({baseURL=assetBase,fetchImpl=(...a)=>fetch(...a),loadArrayBuffer,loaderFactory=()=>new GLTFLoader()}={}){
 const base=new URL(baseURL,import.meta.url),bytes=new Map(),meta=new Map();let catalog;
 async function json(path){const r=await fetchImpl(new URL(path,base));if(!r.ok)throw new Error(`HTTP ${r.status}: ${path}`);return r.json();}
 async function getCatalog(){if(!catalog)catalog=json('catalog.json').catch(e=>{catalog=null;throw e;});return catalog;}
 async function getMetadata(id){const c=await getCatalog(),entry=c.tools.find(t=>t.toolId===id||t.toolType===id);if(!entry)throw new Error('未知刀具：'+id);if(!meta.has(entry.toolId))meta.set(entry.toolId,json(entry.metadataPath).catch(e=>{meta.delete(entry.toolId);throw e;}));return meta.get(entry.toolId);}
 async function loadToolModel(id){const m=await getMetadata(id),url=new URL(m.modelPath,base).href;if(!bytes.has(url))bytes.set(url,(loadArrayBuffer?Promise.resolve().then(()=>loadArrayBuffer(url)):fetchImpl(url).then(r=>{if(!r.ok)throw new Error(`GLB HTTP ${r.status}`);return r.arrayBuffer();})).catch(e=>{bytes.delete(url);throw e;}));const buffer=await bytes.get(url);if(!(buffer instanceof ArrayBuffer))throw new Error('IO必须返回ArrayBuffer');const gltf=await loaderFactory().parseAsync(buffer,new URL('.',url).href),model=new T.Group(),c=new T.Group();c.name='metres-Yup_to_mm-Zup';c.matrix.copy(conversion);c.matrixAutoUpdate=false;c.add(gltf.scene);model.add(c);model.name=m.toolId;model.userData.asset={metadata:m,disposed:false};
 model.traverse(o=>{if(o.isMesh){let p=o;while(p&&!p.userData.componentRole)p=p.parent;if(!p)throw new Error('部件缺少角色：'+o.name);o.userData.partName=p.name;o.userData.componentRole=p.userData.componentRole;}});model.updateMatrixWorld(true);return model;}
 async function getToolTipPosition(id){return new T.Vector3(...(await getMetadata(id)).cuttingReferencePoint);}
 async function getMountingReference(id){return new T.Vector3(...(await getMetadata(id)).mountingOrigin);}
 return{getCatalog,getMetadata,loadToolModel,getToolTipPosition,getMountingReference,clearCache(){bytes.clear();meta.clear();catalog=null;},cacheInfo:()=>({byteEntries:bytes.size,metadataEntries:meta.size})};
}
function data(model){if(!model?.userData.asset||model.userData.asset.disposed)throw new Error('刀具实例已失效');return model.userData.asset.metadata;}
export function getComponents(model,role){data(model);const parts=[];model.traverse(o=>{if(o.isMesh&&o.userData.componentRole&&(!role||o.userData.componentRole===role))parts.push(o);});return parts;}
export function getCuttingReferenceWorld(model,out=new T.Vector3()){const m=data(model);model.updateWorldMatrix(true,false);return model.localToWorld(out.fromArray(m.cuttingReferencePoint));}
export function getBoundingBox(model){data(model);model.updateWorldMatrix(true);const box=new T.Box3(),p=new T.Vector3();for(const o of getComponents(model)){const a=o.geometry.attributes.position;for(let i=0;i<a.count;i++)box.expandByPoint(p.fromBufferAttribute(a,i).applyMatrix4(o.matrixWorld));}return box;}
export function applyToolTransform(model,matrix){data(model);const m=matrix?.isMatrix4?matrix:new T.Matrix4().fromArray(matrix);if(!m.elements.every(Number.isFinite)||Math.abs(m.determinant())<1e-12)throw new Error('无效安装矩阵');model.matrix.copy(m);model.matrixAutoUpdate=false;model.updateWorldMatrix(true,true);return model;}
export function disposeToolModel(model){if(!model?.userData.asset||model.userData.asset.disposed)return;const gs=new Set(),ms=new Set(),ts=new Set();model.traverse(o=>{if(o.geometry)gs.add(o.geometry);for(const m of(Array.isArray(o.material)?o.material:[o.material]))if(m){ms.add(m);for(const v of Object.values(m))if(v?.isTexture)ts.add(v);}});for(const t of ts)t.dispose();for(const m of ms)m.dispose();for(const g of gs)g.dispose();model.removeFromParent();model.clear();model.userData.asset.disposed=true;}
export const library=createToolLibrary();
export const loadToolModel=(id)=>library.loadToolModel(id);
export const getToolTipPosition=(id)=>library.getToolTipPosition(id);
export const getMountingReference=(id)=>library.getMountingReference(id);
