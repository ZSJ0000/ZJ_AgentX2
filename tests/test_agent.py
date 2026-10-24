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
