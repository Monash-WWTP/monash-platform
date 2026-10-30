/* Debug APK only. Forward the app's Android WebView DevTools socket to TCP 9223.
 * Uses Node 22's built-in WebSocket, no dependencies; only the local water target. */
const fs=require('node:fs');
(async()=>{
  const targets=await(await fetch('http://127.0.0.1:9223/json/list')).json();
  const target=targets.find(t=>t.url.startsWith('https://water.citizenflood.invalid/'));
  if(!target)throw new Error('No local water WebView target');
  const ws=new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=reject;});
  const expression=process.argv[2]==='--file'?fs.readFileSync(process.argv[3],'utf8'):process.argv[3];
  if(!expression)throw new Error('Use --file FILE or --expression EXPRESSION');
  const result=await new Promise((resolve,reject)=>{
    const timer=setTimeout(()=>reject(new Error('DevTools evaluation timed out')),15000);
    ws.onmessage=event=>{const message=JSON.parse(event.data);if(message.id===1){clearTimeout(timer);resolve(message);}};
    ws.send(JSON.stringify({id:1,method:'Runtime.evaluate',params:{expression,returnByValue:true,awaitPromise:true}}));
  }).finally(()=>ws.close());
  if(result.result?.exceptionDetails)throw new Error(JSON.stringify(result.result.exceptionDetails));
  console.log(JSON.stringify(result));
})().catch(error=>{console.error(error.message);process.exitCode=1;});
