# 使用说明

## 配置

复制 `config.example.json` 为 `config.json`。`api_key` 直接写在项目配置中，也可留空配合本地兼容服务。不要把真实密钥提交到 Git。

## CLI

`python -m zj_agentx2 --task "..."`，或通过 `--config path --workspace path` 指定配置和工作目录。

## 自定义工具

```python
from zj_agentx2 import ToolDefinition, ToolRegistry
registry.register(ToolDefinition("my_tool", "说明", {"type":"object","properties":{},"additionalProperties":False}, lambda a: "ok"))
```

## 自定义模型

实现 `complete(messages, tools)`，返回 `ModelResponse`，即可注入 `AgentRuntime(model=...)`。测试中的 `ScriptedModel` 就是示例。


## MCP

CLI 从 `mcp_servers` 启动 stdio MCP Server，工具注册为 `demo__工具名`，并受 `allowed_tools` 控制。

## 子 Agent 配置

在 `subagents` 中配置 `system_prompt`、`allowed_tools`、`max_rounds` 和 `max_depth`。


## 宿主工具回调

宿主程序可注入回调：

```python
from zj_agentx2 import HostBridge, HostToolBridge
host = HostBridge({"ask_user": lambda payload: {"answer": "yes"}})
HostToolBridge(host).register_tools(registry)
```

高风险能力（授权、外部确认、发布产物）应由宿主回调显示真实卡片并在用户确认后返回结果。

## MCP 管理

使用 MCP_TEMPLATES 配置自定义或 GitHub stdio MCP；GitHub MCP 需要用户自行提供令牌。

## 页面配置

`web.host` 默认 `127.0.0.1`；需要局域网访问时改为 `0.0.0.0`，同时建议开启密码。`auth_mode` 可设为 `text` 或 `pattern`。当前 pattern 提供验证协议，图形点选界面仍需后续 UI 增强。

## 长任务

长任务在后台线程运行，页面可以查看状态并点击停止。即使开启长任务，也保留最大周期安全上限。
