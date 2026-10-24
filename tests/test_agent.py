import os, tempfile, unittest
from zj_agentx2 import *
from zj_agentx2.core import AgentConfig

class AgentTests(unittest.TestCase):
 def test_tool_loop(self):
  m=ScriptedModel(['{"type":"tool_call","name":"calculator","arguments":{"expression":"12*8"}}','{"type":"final","content":"结果是 96"}'])
  r=AgentRuntime(build_default_registry(tempfile.mkdtemp()),m); self.assertEqual(r.run('x',AgentConfig()),'结果是 96')
 def test_permission_and_delegate(self):
  m=ScriptedModel(['{"type":"tool_call","name":"delegate","arguments":{"agent":"math","task":"算一下"}}','{"type":"final","content":"完成"}'])
  sub=AgentConfig(name='math', allowed_tools=['calculator'])
  r=AgentRuntime(build_default_registry(tempfile.mkdtemp()),m)
  # shared scripted model: delegated call consumes next response
  self.assertEqual(r.run('x',AgentConfig(allowed_tools=['delegate'],subagents={'math':sub})),'完成')
 def test_path_escape(self):
  r=build_default_registry(tempfile.mkdtemp())
  with self.assertRaises(ValueError): r.execute('read_file',{'path':'../x'})
 def test_schema(self):
  r=build_default_registry(tempfile.mkdtemp())
  with self.assertRaises(ValueError): r.execute('calculator',{'expression':'1','bad':2})
if __name__=='__main__': unittest.main()

class AddedFeatureTests(unittest.TestCase):
 def test_native_tool_call(self):
  class M:
   def __init__(self): self.n=0
   def complete(self,m,t):
    from zj_agentx2.core import ModelResponse
    self.n+=1
    return ModelResponse(tool_calls=[{'id':'1','name':'calculator','arguments':{'expression':'2+3'}}]) if self.n==1 else ModelResponse('{"type":"final","content":"5"}')
  self.assertEqual(AgentRuntime(build_default_registry(tempfile.mkdtemp()),M()).run('x',AgentConfig()),'5')
 def test_config_subagent(self):
  import json
  from zj_agentx2.config import load_config
  p=os.path.join(tempfile.mkdtemp(),'c.json')
  with open(p,'w') as f: f.write(json.dumps({'subagents':{'math':{'allowed_tools':['calculator']}}}))
  self.assertEqual(load_config(p)[1].subagents['math'].allowed_tools,['calculator'])
 def test_mcp_bridge(self):
  from zj_agentx2.mcp import MCPToolBridge
  class F:
   def list_tools(self): return [{'name':'echo','inputSchema':{'type':'object','properties':{'text':{'type':'string'}},'required':['text']}}]
   def call_tool(self,n,a): return {'content':[{'type':'text','text':a['text']}]}
  r=ToolRegistry(); self.assertEqual(MCPToolBridge(F(),'demo').register_tools(r),['demo__echo']); self.assertEqual(r.execute('demo__echo',{'text':'ok'}),'ok')

class ConfigRuntimeTests(unittest.TestCase):
 def test_mcp_timeout_property_exists(self):
  from zj_agentx2.mcp import MCPStdioClient
  self.assertEqual(MCPStdioClient('no-such-command', timeout=3).timeout,3)

class HostFinalTests(unittest.TestCase):
 def test_host_error_is_structured(self):
  from zj_agentx2.host import HostBridge
  result=HostBridge({'memory':lambda a: (_ for _ in ()).throw(RuntimeError('bad'))}).call('memory',{'action':'list'})
  self.assertEqual(result['status'],'error'); self.assertIn('bad',result['message'])

class ExpansionFinalTests(unittest.TestCase):
 def test_extra_tools(self):
  import json
  r=build_default_registry(tempfile.mkdtemp()); r.execute('write_file',{'path':'a.txt','content':'x'}); self.assertIn('a.txt',r.execute('find_files',{'pattern':'**/*.txt'})); self.assertEqual(r.get('list_dir').risk,'medium'); self.assertIn('characters',json.loads(r.execute('text_stats',{'text':'a b'})))
 def test_mcp_templates(self):
  from zj_agentx2.mcp_manager import MCP_TEMPLATES
  self.assertIn('github',MCP_TEMPLATES); self.assertIn('custom',MCP_TEMPLATES)

class FinalGUIWebTests(unittest.TestCase):
 def test_web_auth(self):
  from zj_agentx2.web import WebConfig,AuthManager
  self.assertTrue(AuthManager(WebConfig(password='abc')).verify('abc')); self.assertFalse(AuthManager(WebConfig(password='abc')).verify('bad')); self.assertTrue(AuthManager(WebConfig(auth_enabled=False)).verify('x'))
 def test_web_pattern_and_gui_import(self):
  from zj_agentx2.web import WebConfig,AuthManager
  self.assertTrue(AuthManager(WebConfig(auth_mode='pattern',pattern='1,2,3')).verify('1,2,3'))
  import zj_agentx2.gui as g
  self.assertTrue(hasattr(g,'run_gui'))

class LongTaskFinalTests(unittest.TestCase):
 def test_core_stop_tool(self):
  from zj_agentx2.core import AgentRuntime,AgentConfig,ScriptedModel
  m=ScriptedModel(['{"type":"final","content":"phase"}','{"type":"tool_call","name":"long_task_stop","arguments":{"stop":true}}']); x=AgentRuntime(build_default_registry(tempfile.mkdtemp()),m).run_long_task('x',AgentConfig(),max_cycles=2); self.assertEqual(x['stop_reason'],'user_or_tool_stop')
 def test_web_background_stop(self):
  from zj_agentx2.web import AgentWebServer,WebConfig
  def r(t,e,n): e.set(); return {'result':'ok','cycles':1,'stop_reason':'user_or_tool_stop'}
  s=AgentWebServer(WebConfig(auth_enabled=False),long_runner=r); s.start_task('x',True); s.task_thread.join(1); self.assertEqual(s.task['state'],'completed'); self.assertEqual(s.task['result'],'ok')

class PlatformMechanismTests(unittest.TestCase):
 def test_manifest_and_context(self):
  from zj_agentx2.platform import load_manifest, model_context
  m=load_manifest(); self.assertEqual(m['name'],'ZJ AgentX2'); self.assertIn('host_callbacks_required',model_context(m))
 def test_platform_tool(self):
  import json
  r=build_default_registry(tempfile.mkdtemp()); self.assertEqual(json.loads(r.execute('platform_info',{}))['edition'],'personal')
 def test_agent_context(self):
  from zj_agentx2.core import AgentRuntime,AgentConfig,ScriptedModel
  m=ScriptedModel(['{"type":"final","content":"ok"}']); AgentRuntime(build_default_registry(tempfile.mkdtemp()),m).run('x',AgentConfig()); self.assertIn('Platform capability manifest',m.last_messages[0]['content'])
