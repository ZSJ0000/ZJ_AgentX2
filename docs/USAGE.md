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
