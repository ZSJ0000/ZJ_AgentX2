from __future__ import print_function
import argparse,os,shutil,subprocess,sys
ROOT=os.path.abspath(os.path.dirname(__file__)); VENV=os.path.join(ROOT,'.venv'); PYTHON=os.path.join(VENV,'Scripts','python.exe') if os.name=='nt' else os.path.join(VENV,'bin','python')
def run(command,label): print('[deploy] '+label); return subprocess.call(command,cwd=ROOT)
def main(argv=None):
 p=argparse.ArgumentParser(description='Deploy ZJ AgentX2 in the project directory'); p.add_argument('--no-venv',action='store_true'); p.add_argument('--skip-tests',action='store_true'); p.add_argument('--start',action='store_true'); p.add_argument('--task',default='')
 try:a=p.parse_args(argv)
 except SystemExit as e:return int(e.code)
 py=sys.executable
 if not a.no_venv:
  if not os.path.exists(VENV):
   code=run([sys.executable,'-m','venv',VENV],'create project-local virtual environment')
   if code:return code
  if not os.path.exists(PYTHON):print('[deploy] virtual environment Python was not found');return 2
  py=PYTHON
 cfg=os.path.join(ROOT,'config.json')
 if not os.path.exists(cfg):shutil.copyfile(os.path.join(ROOT,'config.example.json'),cfg);print('[deploy] created config.json')
 os.makedirs(os.path.join(ROOT,'workspace'),exist_ok=True)
 if not a.skip_tests:
  code=run([py,'-m','unittest','discover','-s','tests','-v'],'run tests')
  if code:print('[deploy] tests failed; deployment stopped');return code
 print('[deploy] deployment completed');print('[deploy] edit: '+cfg)
 if a.start:return run([py,'-m','zj_agentx2','--config',cfg,'--task',a.task or '请介绍当前平台能力'],'start Agent')
 return 0
if __name__=='__main__':sys.exit(main())
