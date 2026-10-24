import argparse, time, webbrowser
from .config import load_config
from .core import AgentRuntime,OpenAIModel
from .tools import build_default_registry
from .mcp_manager import MCPManager
from .web import AgentWebServer, WebConfig

def main():
 p=argparse.ArgumentParser(); p.add_argument('--config',default='config.json'); p.add_argument('--task'); p.add_argument('--workspace'); p.add_argument('--mode',choices=['auto','gui','web','cli']); a=p.parse_args()
 raw,cfg=load_config(a.config); r=build_default_registry(a.workspace or raw.get('workspace','workspace')); m=MCPManager(r,raw.get('mcp_servers',[])); m.connect_all()
 mode=a.mode or raw.get('startup_mode','auto'); web_cfg=WebConfig.from_dict(raw.get('web',{}))
 if mode=='auto': mode='gui' if raw.get('gui',{}).get('enabled',True) else ('web' if web_cfg.enabled else 'cli')
 stream=bool(raw.get('stream',False)); output=bool(raw.get('stream_output',stream)); sink=[None]
 def on_token(text):
  if mode=='cli': print(text,end='',flush=True)
  elif sink[0]: sink[0](text)
 model=OpenAIModel(raw['base_url'],raw.get('api_key',''),raw['model'],raw.get('timeout_seconds',60),stream=stream,on_token=on_token if output else None)
 runtime=AgentRuntime(r,model); web_server=None
 def run_task(task,event=None): return runtime.run(task,cfg,stop_event=event)
 def run_long(task,event,limit): return runtime.run_long_task(task,cfg,stop_event=event,max_cycles=limit)
 try:
  if mode in ('gui','web'):
   if not web_cfg.enabled: raise RuntimeError('web.enabled must be true for GUI/Web mode')
   web_server=AgentWebServer(web_cfg,agent_runner=run_task,long_runner=run_long,max_long_cycles=int(raw.get('max_long_cycles',1000)))
   sink[0]=web_server.append_output
   address=web_server.start(); url='http://%s:%s' % address
   if mode=='web':
    print('[ZJ_AgentX2] Web started: '+url); webbrowser.open(url)
    while web_server.server: time.sleep(1)
   else:
    from .gui import run_gui
    print('[ZJ_AgentX2] GUI started; Web: '+url); return run_gui(web_server)
  else:
   if not a.task: p.error('--task is required in cli mode')
   result=runtime.run(a.task,cfg)
   if not output or not stream: print(result)
   elif result: print()
 finally:
  if web_server: web_server.stop()
  m.disconnect_all()
if __name__=='__main__': main()
