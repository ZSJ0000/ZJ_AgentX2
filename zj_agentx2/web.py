import hashlib,hmac,json,secrets,threading,time
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
  e=self.c.pattern if self.c.auth_mode=='pattern' else self.c.password; return hmac.compare_digest(self._d(v),self._d(e))
 def issue(self): return self._d(secrets.token_urlsafe(24))
class AgentWebServer:
 def __init__(self,config=None,status_provider=None,agent_runner=None,long_runner=None,max_long_cycles=1000):
  self.config=config or WebConfig(); self.status_provider=status_provider or (lambda:{}); self.agent_runner=agent_runner; self.long_runner=long_runner; self.max_long_cycles=max_long_cycles; self.auth=AuthManager(self.config); self.server=None; self.sessions=set(); self.logs=[]; self.stop_event=threading.Event(); self.task_thread=None; self.task={'state':'idle','task':None,'long_mode':False,'cycles':0,'result':None,'error':None,'stop_reason':None}
 def status(self): return dict(self.status_provider() or {},task=dict(self.task))
 def start_task(self,task,long_mode=False):
  if self.task_thread and self.task_thread.is_alive(): raise RuntimeError('a task is already running')
  runner=self.long_runner if long_mode else self.agent_runner
  if runner is None: raise RuntimeError(('long' if long_mode else 'normal')+' task runner is not configured')
  self.stop_event.clear(); self.task.update(state='running',task=task,long_mode=long_mode,cycles=0,result=None,error=None,stop_reason=None); self.logs.append({'time':time.time(),'event':'task_started','task':task,'long_mode':long_mode})
  def work():
   try:
    result=runner(task,self.stop_event,self.max_long_cycles) if long_mode else runner(task); self.task.update(state='completed',result=result.get('result') if isinstance(result,dict) else str(result),cycles=result.get('cycles',1) if isinstance(result,dict) else 1,stop_reason=result.get('stop_reason') if isinstance(result,dict) else None); self.logs.append({'time':time.time(),'event':'task_completed'})
   except Exception as e: self.task.update(state='error',error=str(e)); self.logs.append({'time':time.time(),'event':'task_error','error':str(e)})
  self.task_thread=threading.Thread(target=work,daemon=True); self.task_thread.start(); return self.task
 def request_stop(self): self.stop_event.set(); self.task['stop_reason']='user_stop'; return self.task
 def start(self):
  if self.server:
   return self.server.server_address
  owner=self
  class H(BaseHTTPRequestHandler):
   def log_message(self,*a):pass
   def json(self,c,o):
    b=json.dumps(o,ensure_ascii=False).encode(); self.send_response(c); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b)
   def page(self,x):
    b=x.encode(); self.send_response(200); self.send_header('Content-Type','text/html; charset=utf-8'); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b)
   def authok(self):
    if not owner.config.auth_enabled:return True
    return self.headers.get('Cookie','').replace('zj_session=','').split(';')[0] in owner.sessions
   def do_GET(self):
    if self.path=='/login':return self.page('<form method="post"><h2>访问验证</h2><input name=password type=password><button>进入</button></form>')
    if not self.authok(): self.send_response(302); self.send_header('Location','/login'); self.end_headers(); return
    if self.path=='/api/status':return self.json(200,owner.status())
    if self.path=='/api/logs':return self.json(200,owner.logs[-100:])
    self.page('<meta charset=utf-8><title>ZJ AgentX2</title><h1>ZJ AgentX2</h1><p>任务控制台</p><textarea id=t rows=4 cols=60></textarea><br><label><input id=l type=checkbox> 长任务模式</label><button onclick="go()">执行</button><button onclick="stop()">停止</button><pre id=o></pre><script>async function go(){let r=await fetch(\'/api/chat\',{method:\'POST\',headers:{\'Content-Type\':\'application/json\'},body:JSON.stringify({task:t.value,long_mode:l.checked})});o.textContent=JSON.stringify(await r.json(),null,2)}async function stop(){o.textContent=JSON.stringify(await (await fetch(\'/api/stop\',{method:\'POST\'})).json(),null,2)}</script>')
   
   
   
  def do_POST(self):
   from urllib.parse import parse_qs
   n=int(self.headers.get('Content-Length','0')); raw=self.rfile.read(n).decode()
   if self.path=='/login':
    if owner.auth.verify(parse_qs(raw).get('password',[''])[0]): t=owner.auth.issue(); owner.sessions.add(t); self.send_response(302); self.send_header('Set-Cookie','zj_session='+t+'; HttpOnly'); self.send_header('Location','/'); self.end_headers()
    else:self.json(403,{'error':'invalid password'})
    return
   if not self.authok():return self.json(401,{'error':'unauthorized'})
   if self.path=='/api/stop':return self.json(200,owner.request_stop())
   if self.path=='/api/chat':
    try:
     d=json.loads(raw); task=d.get('task','').strip()
     if not task:return self.json(400,{'error':'task is required'})
     return self.json(202,owner.start_task(task,bool(d.get('long_mode',False))))
    except Exception as e:return self.json(409,{'error':str(e)})
   self.json(404,{'error':'not found'})
  self.server=ThreadingHTTPServer((self.config.host,self.config.port),H); threading.Thread(target=self.server.serve_forever,daemon=True).start(); return self.server.server_address
 def stop(self):
  if self.server:self.server.shutdown(); self.server.server_close(); self.server=None
