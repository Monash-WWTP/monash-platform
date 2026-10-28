/* Project-owned procedural textures. No original demo photographs are bundled. */
function makeWaterTextures() {
  function canvas(id){const c=document.getElementById(id);c.width=c.height=256;return c.getContext('2d');}
  const t=canvas('tiles');
  t.fillStyle='#6f8e90';t.fillRect(0,0,256,256);
  for(let y=0;y<8;y++)for(let x=0;x<8;x++){
    const v=168+((x*13+y*7)%15);t.fillStyle=`rgb(${v-15},${v+13},${v+17})`;t.fillRect(x*32+1,y*32+1,30,30);
    t.fillStyle='rgba(255,255,255,.16)';t.fillRect(x*32+2,y*32+2,28,1);
  }
  for(const id of ['xneg','xpos','yneg','ypos','zneg','zpos']) {
    const c=canvas(id),g=c.createLinearGradient(0,0,0,256);
    g.addColorStop(0,'#4b7fa7');g.addColorStop(.65,'#accbd5');g.addColorStop(1,'#e3ded0');
    c.fillStyle=g;c.fillRect(0,0,256,256);
    if(id==='yneg'){c.fillStyle='#364e51';c.fillRect(0,0,256,256);continue;}
    for(let i=0;i<18;i++){
      const x=(i*79+id.charCodeAt(0)*13)%300-20,y=(i*37)%150,r=25+(i*11)%45;
      const cloud=c.createRadialGradient(x,y,0,x,y,r);cloud.addColorStop(0,'rgba(255,255,248,.22)');cloud.addColorStop(1,'rgba(255,255,255,0)');
      c.fillStyle=cloud;c.fillRect(x-r,y-r,r*2,r*2);
    }
  }
}
