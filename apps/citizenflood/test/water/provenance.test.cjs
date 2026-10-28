const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const root=path.resolve(__dirname,'../../android/app/src/main/assets/water');
test('bundled Evan Wallace sources match the recorded adaptation and keep MIT notices',()=>{
  const manifest=JSON.parse(fs.readFileSync(path.join(root,'UPSTREAM.json')));
  assert.equal(manifest.commit,'73eda8be832b649367b25ea5690c1f0181bb56ad');
  assert.equal(manifest.license,'MIT');
  for(const [file,record] of Object.entries(manifest.files)){
    const source=fs.readFileSync(path.join(root,'vendor',file));
    assert.equal(crypto.createHash('sha256').update(source).digest('hex'),record.bundledSha256);
    assert.match(source.toString(),/Copyright 2011 Evan Wallace/);
    if(['lightgl.js','cubemap.js'].includes(file))assert.equal(record.upstreamSha256,record.bundledSha256);
  }
  assert.match(fs.readFileSync(path.join(root,'LICENSE.txt'),'utf8'),/Permission is hereby granted, free of charge/);
});
