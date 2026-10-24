# ZJ AgentX2

一个兼容 Python 3.8、Windows 7 的可扩展 Agent 框架：主 Agent 能调用工具，并能把任务委派给受权限限制的子 Agent。

## 特性

- OpenAI 兼容 Chat Completions API；不强制依赖环境变量，配置位于项目目录 `config.json`
- 工具注册与 JSON Schema 参数校验
- 主 Agent 调用工具、创建/调用子 Agent、收集结果
- 子 Agent 独立历史、工具白名单、最大递归层级和超时
- 内置 `calculator`、`read_file`、`write_file`、`http_get`；命令执行工具默认关闭
- CLI、Python API、审计日志、完全离线 fake model 测试

## 快速开始

```bat
copy config.example.json config.json
python -m zj_agentx2 --config config.json --task "计算 12*8，并说明结果"
python -m unittest discover -s tests -v
```

将 `config.json` 中的 `api_key`、`base_url`、`model` 改为你的 OpenAI 兼容服务。配置文件默认不会被提交。

## 工具调用协议

模型应返回 JSON：`{"type":"tool_call","name":"calculator","arguments":{"expression":"12*8"}}`；普通回答返回 `{"type":"final","content":"..."}`。框架也兼容 fenced JSON 和普通文本回退。

## 安全边界

命令执行工具不默认注册；文件工具限制在 `workspace` 目录；HTTP 仅支持 http/https；所有工具参数会先校验。生产环境建议使用低权限账户、容器或沙箱运行。

详见 `docs/DESIGN.md`、`docs/USAGE.md`。


### 配置 MCP 和子 Agent

在 `config.json` 中添加 `mcp_servers`，启动时自动 initialize、tools/list，并注册为 `<name>__<tool>`；`subagents` 可直接配置子 Agent。


## 宿主能力工具

框架提供 `HostBridge` / `HostToolBridge`，可桥接宿主的用户交互和平台能力：`ask_user`、`request_consent`、`load_skill`、`load_mcp_server`、`action_confirmation`、`publish_artifact`、`manage_todos`、`memory`。这些不是伪造的本地实现，而是回调协议；没有宿主回调会明确返回 `unavailable`。CLI 默认关闭，配置 `enable_host_tools: true` 才注册。
