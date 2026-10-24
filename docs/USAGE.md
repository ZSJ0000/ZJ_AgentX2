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

## 平台机制文件

- `PLATFORM.md`：人类可读机制说明。
- `platform_manifest.json`：机器可读能力清单。
- `platform_info`：Agent 查询平台能力的工具。

平台清单不会授予额外权限；实际权限仍由 Agent allowlist、MCP 配置和 HostBridge 回调决定。

## 详细模型提示词与子 Agent 策略

运行时会自动注入工具策略、平台规则、可靠性规则和子 Agent 使用说明。`subagent_policy` 默认是 `prefer_when_complex`：复杂任务优先委派，简单任务直接完成；也可设置 `balanced` 或 `disabled`。委派工具 schema 会列出实际可用的子 Agent 名称，避免模型猜测名称。
