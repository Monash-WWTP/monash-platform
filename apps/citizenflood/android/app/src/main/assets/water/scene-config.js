/* CitizenFlood mobile scene configuration. No reporting/measurement logic. */
(function(root) {
  'use strict';
  function sceneConfig(depth) {
    if(typeof depth!=='number'||!Number.isFinite(depth)||depth<0||depth>1000) throw new Error('Invalid preview depth');
    const worldScaleM=(3+depth)/2;
    const poolHeight=depth/worldScaleM;
    return {worldScaleM,poolHeight,amplitudeNorm:Math.min(.025/worldScaleM,poolHeight*.2),dry:depth===0,
      meshDetail:128,simulationSize:128,causticSize:512};
  }
  function renderSize(width,height,dpr,budget=800000) {
    width=Math.max(1,width||1);height=Math.max(1,height||1);
    const ratio=Math.min(1.5,Math.max(1,dpr||1));
    const scale=Math.min(ratio,Math.sqrt(budget/(width*height)),1440/Math.max(width,height));
    return {width:Math.max(1,Math.floor(width*scale)),height:Math.max(1,Math.floor(height*scale))};
  }
  class SimulationClock {
    constructor(){this.previous=null;this.accumulator=0;}
    tick(now,active){
      if(!active){this.previous=null;this.accumulator=0;return 0;}
      if(this.previous===null){this.previous=now;return 0;}
      this.accumulator+=Math.min(.05,Math.max(0,(now-this.previous)/1000));this.previous=now;
      const steps=Math.min(3,Math.floor((this.accumulator+1e-9)*60));
      this.accumulator-=steps/60;return steps;
    }
  }
  function qualityProfile(level){return [
    {pixels:800000,meshDetail:128,causticSize:512},
    {pixels:400000,meshDetail:96,causticSize:256},
    {pixels:200000,meshDetail:64,causticSize:128}][Math.max(0,Math.min(2,level))];}
  class QualityGovernor {
    constructor(){this.level=0;this.start=null;this.frames=0;this.slowWindows=0;}
    sample(now,rendered,active){
      if(!active){this.start=null;this.frames=0;return null;}
      if(this.start===null)this.start=now;
      if(rendered)this.frames++;
      const elapsed=now-this.start;if(elapsed<4000)return null;
      const fps=this.frames*1000/elapsed;
      let changed=false;
      if(fps<28&&this.level<2){this.level++;changed=true;this.slowWindows=0;}
      else if(fps<15&&this.level===2)this.slowWindows++;
      else this.slowWindows=0;
      this.start=now;this.frames=0;
      return {fps:Math.round(fps*10)/10,level:this.level,changed,tooSlow:this.slowWindows>=2};
    }
  }
  const commands=new Set(['ripple','pause','play','reset','above','underwater','rotateLeft','rotateRight',
    'viewHigher','viewLower','zoomIn','zoomOut','background','foreground']);
  function validCommand(name){return commands.has(name);}
  const api={sceneConfig,renderSize,SimulationClock,validCommand,QualityGovernor,qualityProfile};
  if(typeof module!=='undefined') module.exports=api;
  else root.WaterSceneConfig=api;
})(typeof window==='undefined'?globalThis:window);
