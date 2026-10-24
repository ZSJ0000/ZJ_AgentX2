# ZJ AgentX2 平台机制说明

ZJ AgentX2 是个人版 Agent 平台，可通过 CLI、Web 控制台和可选 PySide2 GUI 运行，不提供多用户注册体系。

## Agent
主 Agent 根据模型响应调用工具；子 Agent 使用独立历史，并受工具白名单、最大轮数和递归深度限制。长任务受停止事件、`long_task_stop` 或安全上限控制。

## 工具与 MCP
内置工具由 ToolRegistry 注册并进行 JSON Schema 校验。MCP 工具通过 stdio JSON-RPC 发现和调用。HostBridge 只是宿主回调协议；没有回调时必须报告 unavailable，不能假装已显示卡片、完成授权或发布产物。

## 安全
文件工具不能越过 workspace；Shell 默认关闭；不得把 API Key、Token、Cookie 或环境变量内容发送给模型或写入日志；外部写入、授权、发布、删除等操作必须由确认机制决定。
