/* CitizenFlood mobile controller for Evan Wallace's MIT WebGL Water renderer.
 * Synthetic local scene only: no networking, camera, capture or reporting APIs. */
'use strict';
var gl, water, renderer, cubemap;
(function(){
  const {sceneConfig,renderSize,SimulationClock,validCommand,QualityGovernor,qualityProfile}=WaterSceneConfig;
  let cfg,clock=new SimulationClock(),paused=false,background=false,dead=false,raf=0;
  let yaw=.65,pitch=.8,zoom=1,underwater=false,underHeight=.45,ambient=0;
  let ruler,rulerShader;
  const governor=new QualityGovernor();let quality=qualityProfile(0);
  const pointers=new Map();let pinchDistance=0,tapStart=null;
  const status=document.getElementById('status');
  const api=window.waterPreview={ready:false,stats:{},command};
  function fail(reason){
    if(dead)return;dead=true;api.ready=false;api.failed=String(reason);cancelAnimationFrame(raf);
    status.textContent='Full water graphics unavailable. Use the basic preview.';
    console.error('WATER_ERROR:'+String(reason).slice(0,160));
  }
  window.addEventListener('error',event=>fail(event.message));
  function resize(){
    const size=renderSize(innerWidth,innerHeight,devicePixelRatio,quality.pixels);
    if(gl.canvas.width===size.width&&gl.canvas.height===size.height)return;
    gl.canvas.width=size.width;gl.canvas.height=size.height;
    gl.viewport(0,0,size.width,size.height);
    const aspect=size.width/size.height;
    gl.matrixMode(gl.PROJECTION);gl.loadIdentity();
    const fov=2*Math.atan(Math.tan(25*Math.PI/180)/Math.min(1,aspect))*180/Math.PI;
    gl.perspective(fov,aspect,.01,100);gl.matrixMode(gl.MODELVIEW);
  }
  function resetCamera(){yaw=.65;pitch=.8;zoom=1;underwater=false;underHeight=.45;}
  function makeRuler(){
    ruler=new GL.Mesh({triangles:false,lines:true,coords:false,normals:false});
    const point=(x,y)=>{ruler.vertices.push([x,y,0]);};
    const segment=(x1,y1,x2,y2)=>{const i=ruler.vertices.length;point(x1,y1);point(x2,y2);ruler.lines.push([i,i+1]);};
    segment(1.08,-cfg.poolHeight,1.08,0);
    const step=Math.max(.1,Number(new URLSearchParams(location.search).get('depthM'))/100)/cfg.worldScaleM;
    for(let i=0;i<=Math.min(100,Math.floor(cfg.poolHeight/step));i++)segment(1.055,-cfg.poolHeight+i*step,1.105,-cfg.poolHeight+i*step);
    ruler.compile();
    rulerShader=new GL.Shader('void main(){gl_Position=gl_ModelViewProjectionMatrix*gl_Vertex;}',
      'void main(){gl_FragColor=vec4(0.9,1.0,0.95,1.0);}');
  }
  function draw(){
    resize();gl.clearColor(.043,.09,.094,1);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);gl.loadIdentity();
    if(underwater){
      const ex=Math.sin(yaw)*.3,ez=Math.cos(yaw)*.3,ey=-cfg.poolHeight*underHeight;
      gl.lookAt(ex,ey,ez,ex-Math.sin(yaw),ey+(.45-underHeight)*.25,ez-Math.cos(yaw),0,1,0);
    }else{
      const d=(3+cfg.poolHeight)*zoom;
      gl.lookAt(Math.sin(yaw)*Math.cos(pitch)*d,-cfg.poolHeight/2+Math.sin(pitch)*d,
        Math.cos(yaw)*Math.cos(pitch)*d,0,-cfg.poolHeight/2,0,0,1,0);
    }
    gl.enable(gl.DEPTH_TEST);renderer.renderCube();
    if(!cfg.dry)renderer.renderWater(water,cubemap);
    gl.disable(gl.DEPTH_TEST);
    if(!underwater&&!cfg.dry)rulerShader.draw(ruler,gl.LINES);
  }
  function normals(){
    water.updateNormals();
    if(!cfg.dry){gl.clearColor(0,0,0,0);renderer.updateCaustics(water);gl.clearColor(.043,.09,.094,1);}
  }
  function ripple(x=0,z=0){
    if(cfg.dry)return;
    water.addDrop(x,z,.055,Math.min(.025,cfg.amplitudeNorm*.7));normals();draw();
  }
  function seed(){
    if(cfg.dry)return;
    for(let i=0;i<12;i++)water.addDrop(Math.sin(i*12.989)*.8,Math.cos(i*7.231)*.8,.035,
      (i%2?1:-1)*Math.min(.008,cfg.amplitudeNorm*.3));
  }
  function frame(now){
    if(dead||background)return;
    try{
      const steps=clock.tick(now,!paused);
      if(!paused&&!cfg.dry&&steps){
        ambient+=steps/60;
        if(ambient>1.2){ambient=0;water.addDrop(Math.sin(now*.00071)*.75,Math.cos(now*.00053)*.75,.035,Math.min(.006,cfg.amplitudeNorm*.25));}
        for(let i=0;i<steps*2;i++)water.stepSimulation();
        normals();draw();
      }
      const report=governor.sample(now,!paused&&!cfg.dry&&steps>0,!paused&&!cfg.dry);
      if(report){
        api.stats={fps:report.fps,width:gl.canvas.width,height:gl.canvas.height,
          caustics:true,underwater,paused,quality:report.level};
        console.info('WATER_STATS:'+JSON.stringify(api.stats));
        if(report.tooSlow){fail('Full graphics too slow on this device');return;}
        if(report.changed){
          quality=qualityProfile(report.level);
          const old=renderer.waterMesh;
          renderer.waterMesh=GL.Mesh.plane({detail:quality.meshDetail});
          for(const group of [old.vertexBuffers,old.indexBuffers])for(const b of Object.values(group))if(b.buffer)gl.deleteBuffer(b.buffer);
          gl.deleteTexture(renderer.causticTex.id);
          renderer.causticTex=new GL.Texture(quality.causticSize,quality.causticSize);
          normals();draw();
        }
      }
      raf=requestAnimationFrame(frame);
    }catch(error){fail(error.message);}
  }
  function start(){if(!dead&&!background){cancelAnimationFrame(raf);raf=requestAnimationFrame(frame);}}
  function command(name){
    if(!validCommand(name)||!api.ready||dead)return false;
    switch(name){
      case 'ripple':ripple();break;
      case 'pause':paused=true;clock.tick(0,false);break;
      case 'play':paused=false;clock.tick(0,false);start();break;
      case 'background':background=true;clock.tick(0,false);governor.sample(0,false,false);cancelAnimationFrame(raf);break;
      case 'foreground':background=false;clock.tick(0,false);start();break;
      case 'underwater':if(!cfg.dry)underwater=true;break;
      case 'above':underwater=false;break;
      case 'rotateLeft':yaw-=.2;break;
      case 'rotateRight':yaw+=.2;break;
      case 'viewHigher':pitch=Math.min(1.35,pitch+.15);underHeight=Math.max(.15,underHeight-.1);break;
      case 'viewLower':pitch=Math.max(.45,pitch-.15);underHeight=Math.min(.85,underHeight+.1);break;
      case 'zoomIn':zoom=Math.max(.65,zoom/1.2);break;
      case 'zoomOut':zoom=Math.min(2,zoom*1.2);break;
      case 'reset':
        resetCamera();paused=false;ambient=0;clock.tick(0,false);
        gl.clearColor(0,0,0,0);
        for(const texture of [water.textureA,water.textureB])texture.drawTo(()=>gl.clear(gl.COLOR_BUFFER_BIT));
        seed();normals();start();break;
    }
    if(!background)draw();
    api.paused=paused;api.underwater=underwater;return true;
  }
  function dropAt(x,y){
    if(underwater||cfg.dry)return;
    const rect=gl.canvas.getBoundingClientRect(),tracer=new GL.Raytracer();
    const ray=tracer.getRayForPixel((x-rect.left)*gl.canvas.width/rect.width,(y-rect.top)*gl.canvas.height/rect.height);
    if(Math.abs(ray.y)<.0001)return;
    const t=-tracer.eye.y/ray.y;if(t<=0)return;
    const p=tracer.eye.add(ray.multiply(t));if(Math.abs(p.x)<1&&Math.abs(p.z)<1)ripple(p.x,p.z);
  }
  try{
    cfg=sceneConfig(Number(new URLSearchParams(location.search).get('depthM')));
    makeWaterTextures();gl=GL.create({antialias:true,powerPreference:'high-performance'});gl.canvas.id='water';
    gl.canvas.setAttribute('aria-label','Illustrative water. Tap for ripples, drag to rotate.');document.body.appendChild(gl.canvas);
    if(!gl.getExtension('OES_standard_derivatives'))throw new Error('Caustic shaders unsupported');
    if(!gl.getParameter(gl.MAX_VERTEX_TEXTURE_IMAGE_UNITS))throw new Error('Vertex textures unsupported');
    gl.clearColor(.043,.09,.094,1);
    water=new Water(cfg);
    if(!water.textureA.canDrawTo()||!water.textureB.canDrawTo())throw new Error('Floating-point render targets unsupported');
    water.dropShader.uniforms({maxAmplitude:cfg.amplitudeNorm});water.updateShader.uniforms({maxAmplitude:cfg.amplitudeNorm});
    renderer=new Renderer(cfg);renderer.sphereCenter=new GL.Vector(0,0,0);renderer.sphereRadius=0;
    for(const shader of [...renderer.waterShaders,renderer.cubeShader,renderer.causticsShader,renderer.sphereShader])shader.uniforms({poolHeight:cfg.poolHeight});
    cubemap=new Cubemap(Object.fromEntries(['xneg','xpos','yneg','ypos','zneg','zpos'].map(id=>[id,document.getElementById(id)])));
    makeRuler();seed();normals();draw();
    if(gl.getError()!==gl.NO_ERROR)throw new Error('Graphics initialization failed');
    gl.canvas.addEventListener('webglcontextlost',event=>{event.preventDefault();fail('Graphics context lost');});
    gl.canvas.addEventListener('pointerdown',event=>{
      gl.canvas.setPointerCapture(event.pointerId);pointers.set(event.pointerId,[event.clientX,event.clientY]);
      tapStart=pointers.size===1?[event.clientX,event.clientY]:null;pinchDistance=0;
    });
    gl.canvas.addEventListener('pointermove',event=>{
      const old=pointers.get(event.pointerId);if(!old)return;
      pointers.set(event.pointerId,[event.clientX,event.clientY]);
      if(pointers.size===2){
        const [a,b]=[...pointers.values()],distance=Math.hypot(a[0]-b[0],a[1]-b[1]);
        if(pinchDistance>0)zoom=Math.max(.65,Math.min(2,zoom*pinchDistance/Math.max(1,distance)));
        pinchDistance=distance;tapStart=null;
      }else{
        yaw+=(event.clientX-old[0])*.008;pitch=Math.max(.45,Math.min(1.35,pitch+(event.clientY-old[1])*.008));
        if(tapStart&&Math.hypot(event.clientX-tapStart[0],event.clientY-tapStart[1])>8)tapStart=null;
      }
      draw();
    });
    function release(event){
      if(tapStart&&pointers.size===1)dropAt(event.clientX,event.clientY);
      pointers.delete(event.pointerId);tapStart=null;pinchDistance=0;
    }
    gl.canvas.addEventListener('pointerup',release);gl.canvas.addEventListener('pointercancel',()=>{pointers.clear();tapStart=null;pinchDistance=0;});
    window.addEventListener('resize',()=>{if(!dead)draw();});
    document.addEventListener('visibilitychange',()=>command(document.hidden?'background':'foreground'));
    api.ready=true;api.config=cfg;status.textContent='';console.info('WATER_READY');start();
  }catch(error){fail(error.message);}
})();
