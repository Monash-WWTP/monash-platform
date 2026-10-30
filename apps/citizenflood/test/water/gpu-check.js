/* Run in the bundled scene's browser devtools, while paused/backgrounded.
 * Reads real shader output; not packaged in the APK. */
(()=>{
  waterPreview.command('background');
  const oldColour=gl.getParameter(gl.COLOR_CLEAR_VALUE);
  gl.clearColor(0,0,0,0);
  for(const t of [water.textureA,water.textureB])t.drawTo(()=>gl.clear(gl.COLOR_BUFFER_BIT));
  water.updateNormals();renderer.updateCaustics(water);
  const n=renderer.causticTex.width,rgba=new Uint8Array(n*n*4);
  renderer.causticTex.drawTo(()=>gl.readPixels(0,0,n,n,gl.RGBA,gl.UNSIGNED_BYTE,rgba));
  let minX=n,minY=n,maxX=-1,maxY=-1;
  for(let y=0;y<n;y++)for(let x=0;x<n;x++)if(rgba[(y*n+x)*4+1]>128){minX=Math.min(minX,x);maxX=Math.max(maxX,x);minY=Math.min(minY,y);maxY=Math.max(maxY,y);}
  const caustic={centerX:(minX+maxX+1)/2,centerY:(minY+maxY+1)/2,size:n};
  caustic.pass=Math.abs(caustic.centerX-n/2)<=1&&Math.abs(caustic.centerY-n/2)<=1;
  const fragment=gl.getAttachedShaders(renderer.waterShaders[1].program).find(s=>gl.getShaderParameter(s,gl.SHADER_TYPE)===gl.FRAGMENT_SHADER);
  const program=gl.createProgram(),shaders=[];
  function attach(type,source){const s=gl.createShader(type);gl.shaderSource(s,source);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw new Error(gl.getShaderInfoLog(s));gl.attachShader(program,s);shaders.push(s);}
  attach(gl.VERTEX_SHADER,'attribute vec2 p;varying vec3 position;void main(){position=vec3(0.0);gl_Position=vec4(p,0.0,1.0);}');
  attach(gl.FRAGMENT_SHADER,gl.getShaderSource(fragment));gl.linkProgram(program);
  if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw new Error(gl.getProgramInfoLog(program));
  const out=new GL.Texture(1,1),pixel=new Uint8Array(4),buffer=gl.createBuffer();
  gl.disable(gl.DEPTH_TEST);gl.disable(gl.CULL_FACE);
  out.drawTo(()=>{
    gl.useProgram(program);
    const loc=name=>gl.getUniformLocation(program,name);
    water.textureA.bind(0);renderer.tileTexture.bind(1);cubemap.bind(2);renderer.causticTex.bind(3);
    for(const [key,index]of Object.entries({water:0,tiles:1,sky:2,causticTex:3}))gl.uniform1i(loc(key),index);
    gl.uniform3f(loc('eye'),.9,-.1,0);gl.uniform3f(loc('sphereCenter'),0,0,0);gl.uniform1f(loc('sphereRadius'),0);
    gl.uniform1f(loc('poolHeight'),waterPreview.config.poolHeight);
    gl.uniform3f(loc('light'),renderer.lightDir.x,renderer.lightDir.y,renderer.lightDir.z);
    gl.bindBuffer(gl.ARRAY_BUFFER,buffer);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,1,1]),gl.STATIC_DRAW);
    const p=gl.getAttribLocation(program,'p');gl.enableVertexAttribArray(p);gl.vertexAttribPointer(p,2,gl.FLOAT,false,0,0);
    gl.drawArrays(gl.TRIANGLE_STRIP,0,4);gl.readPixels(0,0,1,1,gl.RGBA,gl.UNSIGNED_BYTE,pixel);gl.disableVertexAttribArray(p);
  });
  const totalInternalReflection={pixel:[...pixel],pass:pixel[0]+pixel[1]+pixel[2]>10};
  gl.deleteBuffer(buffer);gl.deleteTexture(out.id);gl.deleteProgram(program);shaders.forEach(s=>gl.deleteShader(s));
  gl.clearColor(...oldColour);
  const result={caustic,totalInternalReflection,error:gl.getError()};
  waterPreview.command('reset');waterPreview.command('background');
  return result;
})()
