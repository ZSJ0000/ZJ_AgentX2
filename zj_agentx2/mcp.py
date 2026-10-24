import json, subprocess, threading, time
class MCPError(Exception): pass
class MCPStdioClient:
 def __init__(self,command,args=None,env=None,cwd=None,timeout=30): self.command,self.args,self.env,self.cwd,self.timeout=command,args or [],env,cwd,timeout; self.proc=None; self.n=1; self.lock=threading.Lock()
 def start(self):
  if self.proc:return
  self.proc=subprocess.Popen([self.command]+self.args,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,cwd=self.cwd,env=self.env,bufsize=0)
  self._request('initialize',{'protocolVersion':'2024-11-05','capabilities':{},'clientInfo':{'name':'ZJ_AgentX2','version':'1.0'}}); self._notify('notifications/initialized',{})
 def close(self):
  if self.proc:
   self.proc.terminate(); self.proc=None
 def list_tools(self): self.start(); return self._request('tools/list',{}).get('tools',[])
 def call_tool(self,name,arguments): self.start(); return self._request('tools/call',{'name':name,'arguments':arguments})
 def _notify(self,m,p): self._send({'jsonrpc':'2.0','method':m,'params':p})
 def _request(self,m,p):
  with self.lock:
   i=self.n; self.n+=1; self._send({'jsonrpc':'2.0','id':i,'method':m,'params':p})
   deadline=time.time()+self.timeout
   while 1:
    if time.time()>deadline: raise MCPError('MCP request timeout')
    x=self._receive()
    if x.get('id')!=i: continue
    if 'error' in x: raise MCPError(str(x['error']))
    return x.get('result',{})
 def _send(self,x):
  if not self.proc: raise MCPError('MCP process is not running')
  b=json.dumps(x,separators=(',',':')).encode(); self.proc.stdin.write(('Content-Length: %d\r\n\r\n'%len(b)).encode()+b); self.proc.stdin.flush()
 def _receive(self):
  h={}
  while 1:
   line=self.proc.stdout.readline()
   if not line: raise MCPError('MCP server closed stdout')
   line=line.decode('ascii','replace').strip()
   if not line: break
   if ':' in line: k,v=line.split(':',1); h[k.lower()]=v.strip()
  n=int(h.get('content-length','0'))
  if not n: raise MCPError('MCP response missing Content-Length')
  return json.loads(self.proc.stdout.read(n).decode())
class MCPToolBridge:
 def __init__(self,client,prefix='mcp'): self.client,self.prefix,self.remote_names=client,prefix,{}
 def register_tools(self,registry):
  from .tools import ToolDefinition
  for x in self.client.list_tools():
   name=self.prefix+'__'+x['name']; self.remote_names[name]=x['name']; registry.register(ToolDefinition(name,'MCP: '+x.get('description',x['name']),x.get('inputSchema',{'type':'object'}),self._handler(name)))
  return list(self.remote_names)
 def _handler(self,name):
  def f(args):
   r=self.client.call_tool(self.remote_names[name],args)
   if r.get('isError'): raise MCPError(self._text(r))
   return self._text(r)
  return f
 def _text(self,r): return '\n'.join(x.get('text','') for x in r.get('content',[]) if x.get('type')=='text') or json.dumps(r,ensure_ascii=False)
