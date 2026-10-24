from .mcp import MCPStdioClient,MCPToolBridge
MCP_TEMPLATES={'custom':{'name':'custom','command':'python','args':['path/to/server.py']},'github':{'name':'github','command':'npx','args':['-y','@modelcontextprotocol/server-github'],'env':{'GITHUB_PERSONAL_ACCESS_TOKEN':''}}}
class MCPServerStatus:
 def __init__(self,name,state,tools=None,error=None): self.name,self.state,self.tools,self.error=name,state,tools or [],error
 def as_dict(self): return {'name':self.name,'state':self.state,'tools':self.tools,'error':self.error}
class MCPManager:
 def __init__(self,registry,definitions=None): self.registry,self.definitions=registry,definitions or []; self.clients={}; self.statuses={}
 def connect_all(self):
  for x in self.definitions:
   if x.get('enabled',True): self.connect(x)
  return self.status()
 def connect(self,x):
  n=x.get('name') or 'mcp'
  try:
   c=MCPStdioClient(x['command'],x.get('args',[]),x.get('env'),x.get('cwd'),x.get('timeout_seconds',30)); names=MCPToolBridge(c,n).register_tools(self.registry); self.clients[n]=c; self.statuses[n]=MCPServerStatus(n,'connected',names)
  except Exception as e:self.statuses[n]=MCPServerStatus(n,'error',error=str(e))
  return self.statuses[n].as_dict()
 def disconnect_all(self):
  for c in self.clients.values():c.close()
  self.clients.clear()
 def status(self):return [x.as_dict() for x in self.statuses.values()]
