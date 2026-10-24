import json
SUBAGENT_GUIDE='''\n## 子 Agent 使用策略（必须遵守）\n你可以使用 `delegate` 工具调用子 Agent。只要配置中存在可用子 Agent，就应在复杂任务中主动使用。研究、网页检索、文件分析、代码审查、数据整理、独立验证、多个专业角色或长任务优先委派；简单计算、简单问答、单个文件简单读取不必委派。\n\n委派格式：{"type":"tool_call","name":"delegate","arguments":{"agent":"子Agent名称","task":"独立、具体、可验证的子任务"}}。只能使用系统列出的名称；子任务要写明目标、范围、输出格式和检查重点；不要原样重复整个任务；返回后必须检查、比较并整合；失败或无权限时说明原因并退化到可用工具；遵守最大深度和轮数；外部写入、授权、发布、删除仍需确认。\n'''
TOOL_GUIDE='''\n## 工具使用策略（必须遵守）\n先判断是否需要工具，选择最小权限工具；文件使用 workspace 相对路径且不得越界；find_files 用于搜索、list_dir 用于目录、text_stats 用于文本、json_format 用于 JSON；http_get 仅用于公开 HTTP/HTTPS 内容；MCP 是远程能力，失败如实报告；Host 工具返回 unavailable/error 时不能声称成功；写文件、修改外部资源、发送、发布、删除前确认；参数必须严格 JSON；必要时用第二个工具或子 Agent 复核。\n'''
OUTPUT_GUIDE='''\n## 输出与可靠性策略\n先完成任务，再总结做了什么、使用了哪些工具/子 Agent、结果、限制和下一步；不泄露密钥、Token、Cookie、密码或环境变量；不声称未成功的操作已完成；错误时停止重复失败调用，修复后验证。\n'''
def build_system_prompt(user_prompt,manifest,tools,subagents,depth,max_depth,policy='prefer_when_complex'):
 names=[x.get('function',{}).get('name','') for x in tools]; agents=list(subagents.keys()); data={'available_tools':names,'available_subagents':agents,'current_depth':depth,'max_depth':max_depth,'subagent_available':bool(agents and depth<max_depth),'subagent_policy':policy}
 return user_prompt+'\n\n'+TOOL_GUIDE+SUBAGENT_GUIDE+OUTPUT_GUIDE+'\n## 当前运行时能力\n'+json.dumps(data,ensure_ascii=False,indent=2)+'\n\n## 平台机制\n'+manifest
