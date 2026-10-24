import argparse
from .config import load_config
from .core import AgentRuntime,OpenAIModel
from .tools import build_default_registry
from .mcp_manager import MCPManager
def main():
 p=argparse.ArgumentParser(); p.add_argument('--config',default='config.json'); p.add_argument('--task',required=True); p.add_argument('--workspace'); a=p.parse_args(); raw,cfg=load_config(a.config); r=build_default_registry(a.workspace or raw.get('workspace','workspace')); m=MCPManager(r,raw.get('mcp_servers',[])); m.connect_all()
 stream=bool(raw.get('stream', False)); output=bool(raw.get('stream_output', stream))
 def on_token(text):
  print(text, end='', flush=True)
 model=OpenAIModel(raw['base_url'],raw.get('api_key',''),raw['model'],raw.get('timeout_seconds',60),stream=stream,on_token=on_token if output else None)
 try:
  result=AgentRuntime(r,model).run(a.task,cfg)
  if not output or not stream: print(result)
  elif result: print()
 finally:m.disconnect_all()
if __name__=='__main__':main()
