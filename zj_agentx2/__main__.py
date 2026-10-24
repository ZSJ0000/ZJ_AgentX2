import argparse
from .config import load_config
from .core import AgentRuntime,OpenAIModel
from .tools import build_default_registry
from .mcp_manager import MCPManager
def main():
 p=argparse.ArgumentParser(); p.add_argument('--config',default='config.json'); p.add_argument('--task',required=True); p.add_argument('--workspace'); a=p.parse_args(); raw,cfg=load_config(a.config); r=build_default_registry(a.workspace or raw.get('workspace','workspace')); m=MCPManager(r,raw.get('mcp_servers',[])); m.connect_all()
 try: print(AgentRuntime(r,OpenAIModel(raw['base_url'],raw.get('api_key',''),raw['model'],raw.get('timeout_seconds',60))).run(a.task,cfg))
 finally:m.disconnect_all()
if __name__=='__main__':main()
