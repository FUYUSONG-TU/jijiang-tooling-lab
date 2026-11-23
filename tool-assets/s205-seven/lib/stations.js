import * as T from 'three';
import {applyToolTransform,getComponents,getCuttingReferenceWorld} from './tools.js';
// 类型来自通用配刀图；这些示意ID不是S205真实T号/轴名/选配标定。
export const stations=Object.freeze({
 'gang-od':{name:'外圆排刀座 · 示意OD',drive:'static',interface:'square-shank',operations:['external-grooving','parting-off','external-threading'],reference:'第3张图G/H/J类排刀位置',configurationVerified:false},
 'axial-static':{name:'端面轴向钻孔座 · 静止类型',drive:'static',interface:'round-shank',operations:['center-drill','twist-drill'],reference:'第3张图钻孔加工示意（K为章节标记，非工位号）',configurationVerified:false},
 'axial-boring':{name:'轴向内孔刀座 · 静止类型',drive:'static',interface:'round-shank',operations:['internal-boring'],reference:'第3张图内径加工示意（F为章节标记，非工位号）',configurationVerified:false},
 'optional-driven':{name:'选配轴向动力刀座 · 条件示意',drive:'driven',interface:'round-shank',operations:['solid-carbide-endmill'],reference:'现有参考图不能确认动力选配，默认禁止装配，需显式开启条件示意',configurationVerified:false,requiresExplicitIllustration:true}
});
export function mountInStation(model,stationId,{allowUnverifiedDriven=false}={}){
 const m=model.userData.asset?.metadata,s=stations[stationId];if(!m||!s)throw new Error('未知刀具或工位');if(!s.operations.includes(m.toolType)||!m.compatibleStationTypes.includes(stationId)||m.mountingInterface.type!==s.interface)throw new Error('机械接口/操作类型不兼容');if(s.requiresExplicitIllustration&&!allowUnverifiedDriven)throw new Error('S205动力头选配未核验：铣刀不能安装到静止钻孔位。显式开启条件动力头示意后才能装配。');
 const radial=stationId==='gang-od',rotation=radial?new T.Matrix4():new T.Matrix4().makeRotationZ(-Math.PI/2),reference=new T.Vector3(...(radial?m.cuttingReferencePoint:m.axialGaugePoint)),target=radial?new T.Vector3(6,18,0):new T.Vector3(36,0,0),translation=target.clone().sub(reference.applyMatrix4(rotation));rotation.setPosition(translation);applyToolTransform(model,rotation);
 return{stationId,name:s.name,actualMachineVerified:false,alignmentReference:radial?'cutting-reference':'tool-axis-gauge-plane',alignmentTarget:target.toArray(),matrixColumnMajor:rotation.toArray(),physicalMeaning:radial?'外圆刀在安全径向位置，未切削':'轴向刀具与主轴中心线平行/重合，前端停在端面外12mm',referenceEvidence:s.reference};
}
export function inspectStationClearance(model){const m=model.userData.asset.metadata;model.updateWorldMatrix(true);let workHits=0,guideHits=0,minSurfaceDistance=Infinity,pointCount=0;const p=new T.Vector3();function test(q){pointCount++;const radius=Math.hypot(q.y,q.z);if(q.x>=-100&&q.x<=24){minSurfaceDistance=Math.min(minSurfaceDistance,radius-8);if(radius<8-.025)workHits++;}if(q.x>=-8&&q.x<=0&&radius>8.15&&radius<19)guideHits++;}
 // Vertices and triangle centroids: finite samples, not CAD collision certification.
 for(const o of getComponents(model)){const a=o.geometry.attributes.position,idx=o.geometry.index;for(let i=0;i<a.count;i++)test(p.fromBufferAttribute(a,i).applyMatrix4(o.matrixWorld));const n=idx?idx.count:a.count;for(let i=0;i<n;i+=3){const q=new T.Vector3();for(let j=0;j<3;j++)q.add(new T.Vector3().fromBufferAttribute(a,idx?idx.getX(i+j):i+j).applyMatrix4(o.matrixWorld));test(q.multiplyScalar(1/3));}}
 const axisOrigin=new T.Vector3(0,0,0).applyMatrix4(model.matrixWorld),axisEnd=new T.Vector3(0,-1,0).applyMatrix4(model.matrixWorld),direction=axisEnd.sub(axisOrigin).normalize();const radial=m.compatibleStationTypes.includes('gang-od');return{workHits,guideHits,pointCount,axisParallelError:radial?null:Math.hypot(direction.y,direction.z),axisCenterlineError:radial?null:Math.hypot(axisOrigin.y,axisOrigin.z),cuttingReferenceWorld:getCuttingReferenceWorld(model).toArray(),inspectionState:'停放装配；无加工运动',limitations:'有限表面点检查，不覆盖连续扫掠/所有实体包含关系/附件干涉'};
}
