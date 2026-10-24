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
 def __init__(self,config=None,status_provider=None,agent_runner=None,long_runner=None,max_long_cycles=1000,reset_callback=None):
  self.config=config or WebConfig(); self.reset_callback=reset_callback; self.status_provider=status_provider or (lambda:{}); self.agent_runner=agent_runner; self.long_runner=long_runner; self.max_long_cycles=max_long_cycles; self.auth=AuthManager(self.config); self.server=None; self.sessions=set(); self.logs=[]; self.stop_event=threading.Event(); self.task_thread=None; self.output=''; self.task={'state':'idle','task':None,'long_mode':False,'cycles':0,'result':None,'error':None,'stop_reason':None}
 def append_output(self,text):
  if text:
   self.output += text
 def status(self):
  x=dict(self.status_provider() or {},task=dict(self.task)); x['output']=self.output; return x
 def start_task(self,task,long_mode=False):
  if self.task_thread and self.task_thread.is_alive(): raise RuntimeError('a task is already running')
  runner=self.long_runner if long_mode else self.agent_runner
  if runner is None: raise RuntimeError(('long' if long_mode else 'normal')+' task runner is not configured')
  self.stop_event.clear(); self.output=''; self.task.update(state='running',task=task,long_mode=long_mode,cycles=0,result=None,error=None,stop_reason=None); self.logs.append({'time':time.time(),'event':'task_started','task':task,'long_mode':long_mode})
  def work():
   try:
    result=runner(task,self.stop_event,self.max_long_cycles) if long_mode else runner(task,self.stop_event); self.task.update(state='completed',result=result.get('result') if isinstance(result,dict) else str(result),cycles=result.get('cycles',1) if isinstance(result,dict) else 1,stop_reason=(result.get('stop_reason') if isinstance(result,dict) and result.get('stop_reason') else self.task.get('stop_reason'))); self.logs.append({'time':time.time(),'event':'task_completed'})
   except Exception as e: self.task.update(state='error',error=str(e)); self.logs.append({'time':time.time(),'event':'task_error','error':str(e)})
  self.task_thread=threading.Thread(target=work,daemon=True); self.task_thread.start(); return self.task
 def request_stop(self):
  if not (self.task_thread and self.task_thread.is_alive()): return self.task
  self.stop_event.set(); self.task['state']='stopping'; self.task['stop_reason']='user_stop'; self.logs.append({'time':time.time(),'event':'task_stop_requested'}); return self.task
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
    return self.send_page(r'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ZJ AgentX2</title><style>
*{box-sizing:border-box}body{margin:0;background:#0b0f14;color:#e7edf5;font:14px Arial,"Microsoft YaHei",sans-serif;height:100vh;overflow:hidden}.app{display:flex;height:100vh}.side{width:280px;background:#10151d;border-right:1px solid #27303b;padding:18px 14px}.logo{font-size:23px;font-weight:bold;color:#61c3ff;padding:8px 12px 25px}.new{width:100%;background:#1b2733;border:1px solid #334354;color:#e9f4ff;border-radius:9px;padding:12px;text-align:left;cursor:pointer;margin-bottom:18px}.nav{color:#b7c5d3;padding:11px 12px}.history{margin-top:22px;color:#8493a3;font-size:12px;border-top:1px solid #27303b;padding:16px 10px 5px}.item{padding:11px 10px;color:#d6e0ea;border-radius:8px;background:#12384a}.main{flex:1;display:flex;flex-direction:column;min-width:0}.head{height:64px;border-bottom:1px solid #27303b;display:flex;align-items:center;justify-content:space-between;padding:0 28px}.model{font-size:17px;font-weight:bold}.model small{color:#8fa0b1;font-weight:normal;margin-left:8px}.status{border:1px solid #344150;border-radius:18px;padding:8px 14px;color:#a9bac9}.status b{color:#75d99a}.chat{flex:1;overflow:auto;padding:30px max(24px,calc((100% - 900px)/2))}.welcome{text-align:center;color:#92a3b5;margin:90px 0}.msg{max-width:860px;margin:0 auto 22px;line-height:1.65;white-space:pre-wrap;word-break:break-word}.msg.user{background:#1a2430;border-radius:12px;padding:14px 17px}.msg.assistant{padding:8px 4px}.composer{max-width:900px;width:calc(100% - 34px);margin:0 auto 12px;border:1px solid #3a4652;border-radius:18px;background:#111820;padding:12px 14px}.composer textarea{width:100%;height:74px;resize:none;background:transparent;border:0;outline:0;color:#f4f7fb;font:15px Arial,"Microsoft YaHei",sans-serif}.actions{display:flex;align-items:center;gap:10px}.actions button{border:0;border-radius:18px;padding:9px 16px;background:#2b8cad;color:white;cursor:pointer;font-weight:bold}.actions button.stop{background:#7f2932}.actions label{color:#9aabba}.notice{text-align:center;color:#748395;font-size:12px;padding-bottom:10px}@media(max-width:700px){.side{width:60px;padding:10px 6px}.side .nav,.side .history,.side .item,.side .new{display:none}.logo{font-size:0}.logo:first-letter{font-size:25px}.head{padding:0 14px}.chat{padding:18px 12px}}
</style></head><body><div class="app"><aside class="side"><div class="logo">⌁ ZJ AgentX2</div><button class="new" onclick="newChat()">＋ 开始新对话</button><div class="nav">◷ 定时任务</div><div class="nav">▧ 工作区</div><div class="history">最近对话</div><div class="item">本地模型对话</div></aside><main class="main"><header class="head"><div class="model">GLM-Edge-1.5B-Chat <small>本地模型⌄</small></div><div id="status" class="status"><b>●</b> 就绪</div></header><section id="chat" class="chat"><div id="welcome" class="welcome">你好，我是 ZJ AgentX2<br><small>本地模型已连接，可以开始对话</small></div></section><div class="composer"><textarea id="task" placeholder="输入消息，按 Ctrl+Enter 发送"></textarea><div class="actions"><button onclick="runTask()">↑ 发送</button><button class="stop" onclick="stopTask()">■ 停止</button><label><input id="long" type="checkbox"> 长任务</label></div></div><div class="notice">本地模型可能会出错，请检查重要信息。</div></main></div><script>
const $=x=>document.getElementById(x);let polling=false;function add(text,kind){let d=document.createElement('div');d.className='msg '+kind;d.textContent=text;$('chat').appendChild(d);$('chat').scrollTop=$('chat').scrollHeight;return d}function setStatus(s){let n={running:'执行中',stopping:'正在停止',error:'错误',completed:'已完成',idle:'就绪'}[s]||s;$('status').innerHTML='<b>●</b> '+n;$('status').style.color=s==='error'?'#fca5a5':s==='running'?'#fbbf24':'#a9bac9'}async function api(u,o){let r=await fetch(u,o),x=await r.json();if(!r.ok)throw Error(x.error||('HTTP '+r.status));return x}async function runTask(){let text=$('task').value.trim();if(!text||polling)return;$('welcome').style.display='none';add(text,'user');$('task').value='';add('正在思考……','assistant');try{await api('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({task:text,long_mode:$('long').checked})});polling=true;poll()}catch(e){add('提交失败：'+e.message,'assistant')}}async function stopTask(){if(!polling)return;setStatus('stopping');try{await api('/api/stop',{method:'POST'});add('已发送停止请求，等待当前模型返回……','assistant');poll()}catch(e){add('停止失败：'+e.message,'assistant')}}async function poll(){try{let x=await api('/api/status'),t=x.task||{};setStatus(t.state||'idle');let a=document.querySelectorAll('.msg.assistant');if((t.output||t.result)&&a.length)a[a.length-1].textContent=t.output||t.result;if(t.error&&a.length)a[a.length-1].textContent='错误：'+t.error;if(t.state==='running'||t.state==='stopping')setTimeout(poll,700);else polling=false}catch(e){setStatus('error');polling=false}}async function newChat(){try{await api('/api/new',{method:'POST'})}catch(e){}$('chat').innerHTML='<div id="welcome" class="welcome">你好，我是 ZJ AgentX2<br><small>本地模型已连接，可以开始对话</small></div>';$('task').focus()}$('task').addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&e.key==='Enter')runTask()});poll();</script></body></html>''')
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
    if self.path=='/api/new':
     if owner.reset_callback: owner.reset_callback()
     return self.send_json(200,{'ok':True})
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
