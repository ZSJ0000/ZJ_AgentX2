import hashlib,hmac,json,secrets,threading,time
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer

class WebConfig:
 def __init__(self,enabled=True,host='127.0.0.1',port=8765,auth_enabled=True,auth_mode='text',password='change-me',pattern='1,2,3,4',secret=None):
  self.enabled,self.host,self.port=enabled,host,int(port); self.auth_enabled,self.auth_mode,self.password,self.pattern=auth_enabled,auth_mode,password,pattern; self.secret=secret or secrets.token_hex(32)
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
  if self.server:return self.server.server_address
  owner=self
  class Handler(BaseHTTPRequestHandler):
   def log_message(self,*a): pass
   def send_json(self,code,obj):
    b=json.dumps(obj,ensure_ascii=False).encode(); self.send_response(code); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b)
   def send_page(self,html,code=200):
    b=html.encode(); self.send_response(code); self.send_header('Content-Type','text/html; charset=utf-8'); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b)
   def authorized(self):
    if not owner.config.auth_enabled:return True
    cookie=self.headers.get('Cookie',''); return any(x.strip().startswith('zj_session=') and x.split('=',1)[1] in owner.sessions for x in cookie.split(';'))
   def do_GET(self):
    if self.path in ('/login','/login/'):
     return self.send_page('<meta charset="utf-8"><form method="post" action="/login"><h2>访问验证</h2><input name="password" type="password"><button type="submit">进入</button></form>')
    if not self.authorized(): self.send_response(302); self.send_header('Location','/login'); self.end_headers(); return
    if self.path=='/api/status':return self.send_json(200,owner.status())
    if self.path=='/api/logs':return self.send_json(200,owner.logs[-100:])
    return self.send_page(r'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ZJ AgentX2 控制台</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#0f172a;color:#e5e7eb;font:14px Arial,"Microsoft YaHei",sans-serif}button{border:0;border-radius:8px;padding:10px 18px;color:#fff;background:#2563eb;cursor:pointer;font-weight:bold}button:hover{background:#3b82f6}button.danger{background:#dc2626}button.secondary{background:#334155}.shell{max-width:1180px;margin:0 auto;padding:24px}.top{display:flex;justify-content:space-between;align-items:center;margin-bottom:22px}.brand{font-size:28px;font-weight:bold}.brand span{color:#60a5fa}.badge{padding:7px 12px;border-radius:20px;background:#14532d;color:#bbf7d0}.grid{display:grid;grid-template-columns:minmax(0,2fr) minmax(260px,1fr);gap:18px}.card{background:#1e293b;border:1px solid #334155;border-radius:14px;padding:18px;box-shadow:0 8px 25px #02061766}.card h2{font-size:16px;margin:0 0 14px}.task{width:100%;min-height:150px;resize:vertical;border:1px solid #475569;border-radius:10px;background:#0b1220;color:#f8fafc;padding:14px;font:15px Arial,"Microsoft YaHei",sans-serif}.toolbar{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-top:14px}.check{display:flex;align-items:center;gap:7px;color:#cbd5e1}.status{display:flex;justify-content:space-between;padding:11px 0;border-bottom:1px solid #334155}.status:last-child{border-bottom:0}.muted{color:#94a3b8}.output{min-height:260px;max-height:460px;overflow:auto;white-space:pre-wrap;word-break:break-word;background:#020617;border:1px solid #334155;border-radius:10px;padding:14px;color:#dbeafe}.log{max-height:220px;overflow:auto;white-space:pre-wrap;color:#94a3b8;font-size:12px}.wide{grid-column:1/-1}.hint{margin-top:10px;color:#94a3b8;font-size:12px}@media(max-width:760px){.shell{padding:12px}.grid{grid-template-columns:1fr}.wide{grid-column:auto}.top{align-items:flex-start;gap:10px;flex-direction:column}}
</style></head><body><main class="shell"><header class="top"><div class="brand">ZJ <span>AgentX2</span></div><div id="badge" class="badge">● 就绪</div></header>
<section class="grid"><div class="card"><h2>任务输入</h2><textarea id="task" class="task" placeholder="输入要交给本地模型的任务……"></textarea><div class="toolbar"><button onclick="runTask()">执行任务</button><button class="danger" onclick="stopTask()">停止任务</button><label class="check"><input id="long" type="checkbox"> 长任务模式</label></div><div class="hint">本地模型连接由 config.json 配置；任务在后台执行，可随时停止。</div></div>
<div class="card"><h2>运行状态</h2><div class="status"><span class="muted">状态</span><b id="state">idle</b></div><div class="status"><span class="muted">任务</span><span id="taskName">无</span></div><div class="status"><span class="muted">周期</span><span id="cycles">0</span></div><div class="status"><span class="muted">模式</span><span id="mode">普通</span></div></div>
<div class="card wide"><h2>输出结果</h2><div id="output" class="output">等待任务……</div></div><div class="card wide"><h2>运行日志</h2><div id="logs" class="log">暂无日志</div></div></section></main>
<script>
const $=id=>document.getElementById(id);function esc(x){return String(x||'')}function setState(x){$('state').textContent=x||'unknown';$('badge').textContent=(x==='running'?'● 执行中':x==='error'?'● 错误':'● '+(x==='completed'?'已完成':'就绪'));$('badge').style.background=x==='running'?'#854d0e':x==='error'?'#7f1d1d':'#14532d'}
async function api(url,opt){let r=await fetch(url,opt);return await r.json()}async function runTask(){let t=$('task').value.trim();if(!t){$('output').textContent='请输入任务';return}$('output').textContent='任务已提交，等待本地模型响应……';let x=await api('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({task:t,long_mode:$('long').checked})});if(x.error)$('output').textContent=x.error;poll()}async function stopTask(){let x=await api('/api/stop',{method:'POST'});$('output').textContent='已请求停止任务';poll()}async function poll(){try{let x=await api('/api/status');let t=x.task||{};setState(t.state);$('taskName').textContent=t.task||'无';$('cycles').textContent=t.cycles||0;$('mode').textContent=t.long_mode?'长任务':'普通';if(t.result)$('output').textContent=esc(t.result);if(t.error)$('output').textContent='错误：'+t.error;let l=await api('/api/logs');$('logs').textContent=l.length?l.map(v=>new Date(v.time*1000).toLocaleTimeString()+'  '+v.event+(v.task?'  '+v.task:'')).join('\n'):'暂无日志'}catch(e){setState('error');$('output').textContent='连接失败：'+e}if($('state').textContent==='running')setTimeout(poll,800)}poll();
</script></body></html>''')
   def do_POST(self):
    from urllib.parse import parse_qs
    n=int(self.headers.get('Content-Length','0')); raw=self.rfile.read(n).decode('utf-8','replace')
    if self.path=='/login':
     if owner.auth.verify(parse_qs(raw).get('password',[''])[0]):
      token=owner.auth.issue(); owner.sessions.add(token); self.send_response(302); self.send_header('Set-Cookie','zj_session='+token+'; HttpOnly'); self.send_header('Location','/'); self.end_headers()
     else:self.send_json(403,{'error':'invalid password'})
     return
    if not self.authorized():return self.send_json(401,{'error':'unauthorized'})
    if self.path=='/api/stop':return self.send_json(200,owner.request_stop())
    if self.path=='/api/chat':
     try:
      d=json.loads(raw); task=d.get('task','').strip()
      if not task:return self.send_json(400,{'error':'task is required'})
      return self.send_json(202,owner.start_task(task,bool(d.get('long_mode',False))))
     except Exception as e:return self.send_json(409,{'error':str(e)})
    return self.send_json(404,{'error':'not found'})
  self.server=ThreadingHTTPServer((self.config.host,self.config.port),Handler); threading.Thread(target=self.server.serve_forever,daemon=True).start(); return self.server.server_address
 def stop(self):
  if self.server:self.server.shutdown(); self.server.server_close(); self.server=None
