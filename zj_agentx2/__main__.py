import argparse
from .config import load_config
from .core import AgentRuntime, OpenAIModel
from .mcp import MCPStdioClient, MCPToolBridge
from .tools import build_default_registry
def main():
 p=argparse.ArgumentParser(); p.add_argument('--config',default='config.json'); p.add_argument('--task',required=True); p.add_argument('--workspace'); a=p.parse_args(); raw,cfg=load_config(a.config); workspace=a.workspace or raw.get('workspace','workspace'); registry=build_default_registry(workspace,raw.get('enable_shell',False)); clients=[]
 for item in raw.get('mcp_servers',[]):
  client=MCPStdioClient(item['command'],item.get('args',[]),item.get('env'),item.get('cwd'),item.get('timeout_seconds',30)); MCPToolBridge(client,item.get('name','mcp')).register_tools(registry); clients.append(client)
 try: print(AgentRuntime(registry,OpenAIModel(raw['base_url'],raw.get('api_key',''),raw['model'],raw.get('timeout_seconds',60))).run(a.task,cfg))
 finally:
  for client in clients: client.close()
if __name__=='__main__': main()
