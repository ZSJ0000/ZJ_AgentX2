# ZJ AgentX2 设计文档

## 1. 目标

提供一个小而清晰的多 Agent 核心：模型负责规划，框架负责工具执行、权限、循环与审计。主 Agent 可以将一个明确子任务委派给子 Agent，子 Agent 不共享主历史，只接收任务和允许使用的工具。

## 2. 核心对象

- `AgentConfig`：名称、系统提示、工具白名单、最大轮数、子 Agent 配置。
- `ToolRegistry`：注册工具定义、JSON Schema、执行函数。
- `ModelClient`：OpenAI 兼容 HTTP 客户端；通过接口可替换为本地模型或测试模型。
- `AgentRuntime`：消息循环、工具调用、子 Agent 委派、超时和审计。
- `SubAgentSpec`：子 Agent 名称、提示词、工具白名单、最大递归深度。

## 3. 执行流程

1. CLI/API 创建 runtime 和主 Agent。
2. 用户任务加入主 Agent 历史。
3. 模型输出 `final` 或 `tool_call`。
4. 框架检查工具是否在白名单、参数是否符合 schema。
5. 普通工具执行后将结果回传模型；`delegate` 创建隔离的子 Agent。
6. 子 Agent 完成后把摘要作为工具结果回到主 Agent。
7. 达到最大轮数、超时或模型返回 final 时结束。

## 4. 安全设计

默认不提供任意命令执行；文件工具解析后必须位于 workspace；工具白名单按 Agent 生效；子 Agent 不能调用未授权工具；递归深度和轮数有限；工具异常转成可审计结果而不泄漏堆栈给模型。

## 5. 已知限制与后续

当前为同步执行、单进程内存历史；HTTP 客户端未实现流式输出；复杂任务可后续加入并行委派、持久化、MCP adapter、重试策略和人工审批工具。
