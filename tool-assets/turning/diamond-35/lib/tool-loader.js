import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

export const TOOL_ID = 'JJ-OD35-SAMPLE-001';
const aliases = { r02:'r02', r04:'r04', r08:'r08', '0.2':'r02', '0.4':'r04', '0.8':'r08' };
const requireVariant = value => {
  const key = aliases[String(value)];
  if (!key) throw new Error(`不支持的鼻圆版本：${value}`);
  return key;
};
/** A library owns only cached immutable bytes. Every load parses fresh instance resources. */
export function createToolLibrary({
  assetBaseURL = new URL('../', import.meta.url),
  fetchImpl = (...args) => fetch(...args),
  loadArrayBuffer = null,
  loaderFactory = () => new GLTFLoader(),
} = {}) {
  const base = new URL(assetBaseURL, import.meta.url);
  if (!base.pathname.endsWith('/')) throw new Error('assetBaseURL 必须以 / 结尾');
  let metadataPromise;
  const bytes = new Map();
  async function metadata(id = TOOL_ID) {
    if (id !== TOOL_ID) throw new Error(`未知刀具：${id}`);
    if (!metadataPromise) metadataPromise = fetchImpl(new URL('metadata/tool.json', base))
      .then(r => { if (!r.ok) throw new Error(`元数据 HTTP ${r.status}`); return r.json(); })
      .catch(e => { metadataPromise = undefined; throw e; });
    const meta = await metadataPromise;
    if (meta.toolId !== TOOL_ID || meta.schemaVersion !== '2.0') throw new Error('元数据版本或toolId不匹配');
    return meta;
  }
  async function buffer(path) {
    const url = new URL(path, base).href;
    if (!bytes.has(url)) bytes.set(url, (loadArrayBuffer ? Promise.resolve().then(() => loadArrayBuffer(url)) : fetchImpl(url).then(r => {
      if (!r.ok) throw new Error(`GLB HTTP ${r.status}`);
      return r.arrayBuffer();
    })).catch(e => { bytes.delete(url); throw e; }));
    return bytes.get(url);
  }
  async function loadToolModel(id = TOOL_ID, variant = 'r04') {
    const key = requireVariant(variant), meta = await metadata(id), entry = meta.noseRadiusVariants[key];
    const data = await buffer(entry.modelPath);
    if (!(data instanceof ArrayBuffer)) throw new Error('加载适配器必须返回ArrayBuffer');
    const gltf = await loaderFactory().parseAsync(data, new URL('.', new URL(entry.modelPath, base)).href);
    const model = new THREE.Group();
    model.name = `${id}:${key}`;
    const conversion = new THREE.Group();
    conversion.name = 'GLTF_metres_Yup_to_local_mm_Zup';
    conversion.matrix.fromArray(meta.geometryUnits.conversionMatrixColumnMajor);
    conversion.matrixAutoUpdate = false;
    conversion.add(gltf.scene); model.add(conversion);
    model.userData.toolAsset = { toolId:id, variant:key, metadata:meta, variantMetadata:entry, disposed:false };
    model.updateMatrixWorld(true);
    return model;
  }
  async function getToolTipPosition(id = TOOL_ID, variant = 'r04') {
    return new THREE.Vector3(...(await metadata(id)).noseRadiusVariants[requireVariant(variant)].cuttingTipPosition);
  }
  async function getMountingReference(id = TOOL_ID) {
    const m = await metadata(id);
    return { point: new THREE.Vector3(...m.mountingReferencePoint), matrix: new THREE.Matrix4().fromArray(m.mountingTransformMatrixColumnMajor), coordinateSystem:m.localCoordinateSystem };
  }
  return { loadToolModel, getToolTipPosition, getMountingReference, getMetadata:metadata,
    clearResourceCache() { bytes.clear(); metadataPromise = undefined; },
    getCacheInfo() { return { byteEntries:bytes.size }; },
  };
}
function asset(model) {
  if (!model?.userData?.toolAsset || model.userData.toolAsset.disposed) throw new Error('模型不是有效的已加载刀具实例');
  return model.userData.toolAsset;
}
/** Matrix is local-to-parent, column-major; translation uses the parent scene's mm convention. */
export function applyToolTransform(model, transform) {
  asset(model);
  let matrix;
  if (transform?.isMatrix4) matrix = transform.clone();
  else if (Array.isArray(transform)) {
    if (transform.length !== 16) throw new Error('矩阵需要16项');
    matrix = new THREE.Matrix4().fromArray(transform);
  } else {
    const { position=[0,0,0], quaternion=[0,0,0,1], scale=1 } = transform || {};
    matrix = new THREE.Matrix4().compose(new THREE.Vector3(...position), new THREE.Quaternion(...quaternion).normalize(), new THREE.Vector3(...(Array.isArray(scale)?scale:[scale,scale,scale])));
  }
  const e = matrix.elements;
  if (!e.every(Number.isFinite) || Math.abs(matrix.determinant())<1e-12 || Math.abs(e[3])+Math.abs(e[7])+Math.abs(e[11])+Math.abs(e[15]-1)>1e-8) throw new Error('需要非奇异仿射变换');
  model.matrix.copy(matrix); model.matrixAutoUpdate=false;
  matrix.decompose(model.position,model.quaternion,model.scale);
  model.updateWorldMatrix(true,true);
  return model;
}
export function getToolTipWorldPosition(model, target=new THREE.Vector3()) {
  const a=asset(model); model.updateWorldMatrix(true,false);
  return model.localToWorld(target.fromArray(a.variantMetadata.cuttingTipPosition));
}
export function getToolComponents(model, role=null) {
  asset(model); const found=[];
  model.traverse(o=>{ if(o.isMesh && ['holder','insert','seat','fastener'].includes(o.userData.componentRole) && (!role || o.userData.componentRole===role)) found.push(o); });
  return found;
}
export function getToolBoundingBox(model, target=new THREE.Box3()) {
  asset(model); model.updateWorldMatrix(true,true); target.makeEmpty();const v=new THREE.Vector3();for(const o of getToolComponents(model)){const p=o.geometry.attributes.position;for(let i=0;i<p.count;i++)target.expandByPoint(v.fromBufferAttribute(p,i).applyMatrix4(o.matrixWorld));}return target;
}
export function disposeToolModel(model) {
  if (!model?.userData?.toolAsset || model.userData.toolAsset.disposed) return;
  const geometries=new Set(), materials=new Set(), textures=new Set();
  model.traverse(o=>{ if(o.geometry)geometries.add(o.geometry); for(const m of (Array.isArray(o.material)?o.material:[o.material])) if(m){materials.add(m);for(const v of Object.values(m))if(v?.isTexture)textures.add(v);} });
  for(const t of textures)t.dispose();for(const m of materials)m.dispose();for(const g of geometries)g.dispose();
  model.removeFromParent();model.clear();model.userData.toolAsset.disposed=true;
}
const defaults=createToolLibrary();
export const loadToolModel=(...args)=>defaults.loadToolModel(...args);
export const getToolTipPosition=(...args)=>defaults.getToolTipPosition(...args);
export const getMountingReference=(...args)=>defaults.getMountingReference(...args);
export const getToolMetadata=(...args)=>defaults.getMetadata(...args);
export const clearResourceCache=()=>defaults.clearResourceCache();
