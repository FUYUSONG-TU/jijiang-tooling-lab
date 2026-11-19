import { TOOL_ID, loadToolModel, applyToolTransform, getToolTipWorldPosition, getToolComponents, disposeToolModel } from '../lib/tool-loader.js';
/** seat is an Object3D in the host's mm scene. This module supplies no machine kinematics. */
export async function createMountedTool(seat, variant='r04', transform={position:[0,0,0]}) {
  if (!seat?.isObject3D) throw new Error('seat需要宿主提供的Object3D刀座');
  let current = await loadToolModel(TOOL_ID,variant), sequence=0, closed=false;
  applyToolTransform(current,transform);seat.add(current);
  return {
    get model(){return current;},
    getTipWorldPosition(target){if(closed)throw new Error('已释放');return getToolTipWorldPosition(current,target);},
    getCollisionCandidates(){return getToolComponents(current);},
    setTransform(t){if(closed)throw new Error('已释放');applyToolTransform(current,t);},
    async replaceVariant(next) {
      if(closed)throw new Error('已释放');
      const request=++sequence, replacement=await loadToolModel(TOOL_ID,next);
      if(closed||request!==sequence){disposeToolModel(replacement);return false;}
      applyToolTransform(replacement,current.matrix);seat.add(replacement);
      const previous=current;current=replacement;disposeToolModel(previous);return true;
    },
    dispose(){if(closed)return;closed=true;++sequence;disposeToolModel(current);},
  };
}
