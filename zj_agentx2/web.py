import hashlib,hmac,json,secrets,threading
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
class WebConfig:
 def __init__(self,enabled=True,host='127.0.0.1',port=8765,auth_enabled=True,auth_mode='text',password='change-me',pattern='1,2,3,4',secret=None): self.enabled,self.host,self.port=enabled,host,int(port); self.auth_enabled,self.auth_mode,self.password,self.pattern=auth_enabled,auth_mode,password,pattern; self.secret=secret or secrets.token_hex(32)
 @classmethod
 def from_dict(cls,x): return cls(**{k:v for k,v in x.items() if k in ('enabled','host','port','auth_enabled','auth_mode','password','pattern','secret')})
class AuthManager:
 def __init__(self,c): self.c=c
 def _d(self,v): return hmac.new(self.c.secret.encode(),v.encode(),hashlib.sha256).hexdigest()
 def verify(self,v):
  if not self.c.auth_enabled:return True
  e=self.c.pattern if self.c.auth_mode=='pattern' else self.c.password
  return hmac.compare_digest(self._d(v),self._d(e))
 def issue(self): return self._d(secrets.token_urlsafe(24))
INDEX='''<!doctype html><meta charset=utf-8><title>ZJ AgentX2</title><style>body{margin:0;font:14px Arial;background:#202124;color:#eee}header{padding:16px 24px;background:#292a2d}main{display:flex;height:calc(100vh - 55px)}aside{width:220px;padding:20px;background:#17181a}.card{padding:14px;margin-bottom:12px;background:#303134;border-radius:8px}section{flex:1;padding:24px}.muted{color:#aeb0b4}</style><header><b>ZJ AgentX2</b><span class=muted>　个人 Agent 控制台</span></header><main><aside><div class=card>Agent<br><span class=muted>主 Agent / 子 Agent</span></div><div class=card>MCP<br><span class=muted>服务器管理</span></div><div class=card>工具<br><span class=muted>权限与风险</span></div><div class=card>日志<br><span class=muted>运行记录</span></div></aside><section><div class=card><h2>欢迎使用 ZJ AgentX2</h2><p class=muted>个人版 Agent 控制台</p></div><pre id=status class=card>loading...</pre></section></main><script>fetch('/api/status').then(r=>r.json()).then(x=>status.textContent=JSON.stringify(x,null,2))</script>'''
class AgentWebServer:
 def __init__(self,config=None,status_provider=None): self.config=config or WebConfig(); self.status_provider=status_provider or (lambda:{'ok':True}); self.auth=AuthManager(self.config); self.server=None; self.sessions=set()
 def start(self):
  owner=self
  class H(BaseHTTPRequestHandler):
   def log_message(self,*a):pass
   def page(self,x):
    b=x.encode(); self.send_response(200); self.send_header('Content-Type','text/html; charset=utf-8'); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b)
   def authok(self):
    if not owner.config.auth_enabled:return True
    token=self.headers.get('Cookie','').replace('zj_session=','').split(';')[0]; return token in owner.sessions
   def do_GET(self):
    if self.path=='/login':return self.page('<form method="post"><h2>访问验证</h2><input name=password type=password><button>进入</button></form>')
    if not self.authok(): self.send_response(302); self.send_header('Location','/login'); self.end_headers(); return
    if self.path=='/api/status':
     b=json.dumps(owner.status_provider(),ensure_ascii=False).encode(); self.send_response(200); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b); return
    self.page(INDEX)
   def do_POST(self):
    if self.path!='/login':self.send_response(404); self.end_headers(); return
    from urllib.parse import parse_qs
    n=int(self.headers.get('Content-Length','0')); v=parse_qs(self.rfile.read(n).decode()).get('password',[''])[0]
    if owner.auth.verify(v):
     t=owner.auth.issue(); owner.sessions.add(t); self.send_response(302); self.send_header('Set-Cookie','zj_session='+t+'; HttpOnly'); self.send_header('Location','/'); self.end_headers()
    else: self.send_response(403); self.end_headers()
  self.server=ThreadingHTTPServer((self.config.host,self.config.port),H); threading.Thread(target=self.server.serve_forever,daemon=True).start(); return self.server.server_address
 def stop(self):
  if self.server:self.server.shutdown(); self.server.server_close(); self.server=None
