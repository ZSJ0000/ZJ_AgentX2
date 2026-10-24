import json
CAPABILITIES={"ask_user":"Ask a structured question card","request_consent":"Request connector authorization","load_skill":"Load a named skill playbook","load_mcp_server":"Load a connected MCP server","action_confirmation":"Request confirmation for an external action","publish_artifact":"Record a delivered artifact","manage_todos":"Update a visible task checklist","memory":"Remember, list, or forget durable user facts"}
class HostBridge:
 def __init__(self,callbacks=None): self.callbacks=callbacks or {}; self.events=[]
 def call(self,capability,arguments):
  if capability not in CAPABILITIES: raise ValueError('unknown host capability: '+capability)
  self.events.append({'capability':capability,'arguments':arguments}); callback=self.callbacks.get(capability)
  if callback is None: return {'ok':False,'status':'unavailable','capability':capability,'message':'host callback is not configured'}
  try: return {'ok':True,'status':'completed','capability':capability,'result':callback(arguments)}
  except Exception as exc: return {'ok':False,'status':'error','capability':capability,'message':str(exc)}
class HostToolBridge:
 def __init__(self,host_bridge,prefix='host'): self.host,self.prefix=host_bridge,prefix
 def register_tools(self,registry):
  from .tools import ToolDefinition
  for capability,description in CAPABILITIES.items():
   name=self.prefix+'__'+capability; schema={'type':'object','properties':{'payload':{'type':'object'}},'required':['payload'],'additionalProperties':False}; registry.register(ToolDefinition(name,description,schema,self._handler(capability)))
  return [self.prefix+'__'+x for x in CAPABILITIES]
 def _handler(self,capability):
  def handler(arguments): return json.dumps(self.host.call(capability,arguments['payload']),ensure_ascii=False)
  return handler
