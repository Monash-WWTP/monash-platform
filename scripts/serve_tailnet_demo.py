"""Loopback-only adapter for this local Tailscale demo; not a production proxy.

Preserves canonical localhost OIDC identity/backchannel configuration while
rewriting browser entry points. No request/cookie/credential logging.
"""
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import http.client, threading, json, socket, select
PAIRS={'http://localhost:8180':'https://asus-dev.tail66f665.ts.net:10575','http://localhost:9100':'https://asus-dev.tail66f665.ts.net:10577'}
def browser_html(data: bytes) -> bytes:
 """Rewrite frontend API configuration, leaving encoded OIDC redirect_uri intact."""
 for local in ('http://localhost:9100/', 'http://127.0.0.1:9100/'):
  data=data.replace(local.encode(),b'https://asus-dev.tail66f665.ts.net:10577/')
 return data

class Proxy(BaseHTTPRequestHandler):
 def log_message(self,*args): pass
 def proxy(self):
  upstream=self.server.upstream
  headers={k:v for k,v in self.headers.items() if k.lower() not in ('host','connection','accept-encoding')}
  headers['Host']='localhost:'+str(upstream)
  headers['X-Forwarded-Host']=headers['Host']
  headers['X-Forwarded-Proto']='http'
  for h in ('Origin','Referer'):
   if h in headers:
    for local,remote in PAIRS.items():
     if headers[h].startswith(remote):headers[h]=local+headers[h][len(remote):]
  if self.headers.get('Upgrade','').lower() == 'websocket':
   return self.tunnel(upstream,headers)
  body=self.rfile.read(int(self.headers.get('Content-Length',0)))
  c=http.client.HTTPConnection('127.0.0.1',upstream,timeout=30)
  try:
   c.request(self.command,self.path,body,headers);r=c.getresponse();data=r.read()
   if upstream == 9100 and 'text/html' in (r.getheader('Content-Type') or ''):
    data=browser_html(data)
   if 'application/json' in (r.getheader('Content-Type') or ''):
    def rewrite(value):
     if isinstance(value,dict):
      for k,v in value.items():
       if k in ('to','redirect','redirect_url','redirect_to') and isinstance(v,str):
        for local,remote in PAIRS.items():
         if v.startswith(local):value[k]=remote+v[len(local):];break
       else:rewrite(v)
     elif isinstance(value,list):
      for item in value:rewrite(item)
    try:
     value=json.loads(data);rewrite(value);data=json.dumps(value).encode()
    except (ValueError,UnicodeError):pass
   self.send_response(r.status)
   for k,v in r.getheaders():
    if k.lower() in ('connection','transfer-encoding','content-length'):continue
    if k.lower()=='location':
     for local,remote in PAIRS.items():
      if v.startswith(local):v=remote+v[len(local):];break
    self.send_header(k,v)
   self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
  except (OSError,http.client.HTTPException):self.send_error(502)
  finally:c.close()
 def tunnel(self, upstream, headers):
  self.close_connection=True
  headers['Connection']='Upgrade'
  remote=socket.create_connection(('127.0.0.1',upstream),timeout=10)
  try:
   request=f'{self.command} {self.path} HTTP/1.1\r\n'+''.join(f'{k}: {v}\r\n' for k,v in headers.items())+'\r\n'
   remote.sendall(request.encode('latin1'))
   response=b''
   while not response.endswith(b'\r\n\r\n'):
    chunk=remote.recv(1)
    if not chunk:raise OSError('Incomplete WebSocket handshake')
    response+=chunk
    if len(response)>32768:raise OSError('Oversized handshake')
   self.connection.sendall(response)
   if b' 101 ' not in response.split(b'\r\n',1)[0]:return
   remote.settimeout(None)
   while True:
    ready,_,_=select.select([self.connection,remote],[],[],60)
    if not ready:continue
    for source in ready:
     chunk=source.recv(65536)
     if not chunk:return
     (remote if source is self.connection else self.connection).sendall(chunk)
  except OSError:pass
  finally:remote.close()
 do_GET=do_POST=do_PUT=do_PATCH=do_DELETE=do_OPTIONS=do_HEAD=proxy
def main():
 for port,upstream in [(8182,8180),(9182,9100)]:
  s=ThreadingHTTPServer(('127.0.0.1',port),Proxy);s.upstream=upstream
  threading.Thread(target=s.serve_forever,daemon=True).start()
 threading.Event().wait()

if __name__ == '__main__':main()
