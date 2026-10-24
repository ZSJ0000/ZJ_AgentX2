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

## 更多工具和 MCP

新增 current_time、uuid、json_format、text_stats、list_dir、find_files、system_info；新增 MCPManager、custom 和 github 模板，支持多 MCP 启用/禁用与失败隔离。

## PySide2 GUI 与 Web

新增 `zj_agentx2/gui.py` 和 `zj_agentx2/web.py`。Web 默认监听 127.0.0.1，可切换 0.0.0.0 供局域网访问；支持关闭验证、文本密码和图形密码数据模式。PySide2 GUI 支持 Web 启停、深浅主题和状态面板。

## 长任务模式

Web `/api/chat` 支持 `long_mode:true`，模型返回完成后会继续执行；模型可调用 `long_task_stop` 且 `stop:true` 停止，用户可通过 `/api/stop` 停止。系统默认安全上限为 1000 个周期，可配置。

## 一键部署

Linux：`sh deploy_linux.sh`；Windows 7/CMD：`deploy_windows.bat`。通用方式：`python deploy.py`。部署会创建项目内 `.venv`、`config.json`、`workspace` 并运行测试；不会覆盖已有配置。详细说明见 `docs/DEPLOY.md`。

## 模型提示词

Agent 会自动获得详细工具使用规则、平台安全机制和子 Agent 委派策略。复杂研究、文件分析、代码审查、独立复核等任务会优先考虑子 Agent；简单任务不会强制拆分。可用 `subagent_policy` 调整策略。

## 仓库外一键安装

Linux：`sh -c "$(curl -fsSL https://raw.githubusercontent.com/ZSJ0000/ZJ_AgentX2/master/install_linux.sh)"`。Windows 7/CMD：先安装 Git，执行 `git clone https://github.com/ZSJ0000/ZJ_AgentX2.git "%USERPROFILE%\ZJ_AgentX2" && "%USERPROFILE%\ZJ_AgentX2\install_windows.bat" --no-venv`。详细参数见 `docs/INSTALL.md`。
