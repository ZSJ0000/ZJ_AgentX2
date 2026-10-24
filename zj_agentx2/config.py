import json
from .core import AgentConfig
def load_config(path):
 with open(path,encoding='utf-8') as f: c=json.load(f)
 def make(x):
  return AgentConfig(x.get('name','main'),x.get('system_prompt','You are a helpful agent.'),x.get('allowed_tools'),x.get('max_rounds',c.get('max_rounds',8)),x.get('max_depth',c.get('max_depth',2)),{k:make(v) for k,v in x.get('subagents',{}).items()})
 return c,make(c)
