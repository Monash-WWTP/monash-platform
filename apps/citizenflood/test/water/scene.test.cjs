const {test} = require('node:test');
const assert = require('node:assert/strict');
const {sceneConfig, renderSize, SimulationClock, validCommand} = require('../../android/app/src/main/assets/water/scene-config.js');
test('pool geometry preserves depth relative to its illustrative width', () => {
  for (const depth of [0, .001, .5, 10, 1000]) {
    const c = sceneConfig(depth);
    assert.ok(Math.abs(c.poolHeight * c.worldScaleM - depth) < 1e-8);
    assert.ok(c.amplitudeNorm * c.worldScaleM <= .025001);
    assert.ok(c.amplitudeNorm <= c.poolHeight * .2);
    assert.equal(c.dry, depth === 0);
  }
  for (const depth of [-1, NaN, Infinity, 1001, '0.5']) assert.throws(() => sceneConfig(depth));
});
test('canvas pixel budget bounds very large and rotated high-DPI surfaces', () => {
  for (const size of [[360,700,3],[2400,1080,4],[8000,8000,8],[1,1,1]]) {
    const s=renderSize(...size);
    assert.ok(s.width*s.height<=800000);
    assert.ok(s.width>0 && s.height>0 && Math.max(s.width,s.height)<=1440);
  }
});
test('simulation uses elapsed time and drops pause/background catch-up', () => {
  const clock=new SimulationClock();
  assert.equal(clock.tick(1000,true),0);
  assert.equal(clock.tick(1000+1000/30,true),2);
  assert.ok(clock.tick(100000,true)<=3);
  clock.tick(100100,false);
  assert.equal(clock.tick(200000,true),0);
});
test('only fixed preview commands are accepted', () => {
  for (const name of ['ripple','pause','play','reset','above','underwater','zoomIn','rotateLeft','background','foreground']) assert.equal(validCommand(name),true);
  for (const name of ['fetch','open','javascript:alert(1)','pause();alert(1)',null]) assert.equal(validCommand(name),false);
});
test('quality reduces bounded work when rendered frames are slow, not when paused', () => {
  const {QualityGovernor,qualityProfile}=require('../../android/app/src/main/assets/water/scene-config.js');
  const q=new QualityGovernor();
  q.sample(0,true,true);
  let report;
  for(let i=1;i<=40;i++) report=q.sample(i*100,true,true)||report;
  assert.equal(report.level,1);assert.equal(report.changed,true);
  assert.ok(qualityProfile(report.level).pixels<800000);
  q.sample(5000,false,false);
  assert.equal(q.sample(100000,true,true),null);
  assert.equal(q.level,1);
});
