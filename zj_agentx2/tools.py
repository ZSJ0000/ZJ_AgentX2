import ast, json, os, urllib.request

class ToolDefinition:
    def __init__(self, name, description, schema, handler):
        self.name, self.description, self.schema, self.handler = name, description, schema, handler

class ToolRegistry:
    def __init__(self): self._tools = {}
    def register(self, tool): self._tools[tool.name] = tool
    def get(self, name): return self._tools.get(name)
    def schemas(self, allowed=None):
        names = allowed if allowed is not None else self._tools.keys()
        return [{"type":"function", "function":{"name":t.name,"description":t.description,"parameters":t.schema}} for n in names if (t:=self.get(n))]
    def execute(self, name, args):
        tool = self.get(name)
        if not tool: raise ValueError("unknown tool: " + name)
        _validate(tool.schema, args, "arguments")
        return tool.handler(args)

def _validate(schema, value, path):
    typ = schema.get("type")
    if typ == "object":
        if not isinstance(value, dict): raise ValueError(path + " must be object")
        for k in schema.get("required", []):
            if k not in value: raise ValueError(path + "." + k + " is required")
        if schema.get("additionalProperties") is False:
            extra = set(value) - set(schema.get("properties", {}))
            if extra: raise ValueError(path + " has unknown fields: " + ",".join(sorted(extra)))
        for k, s in schema.get("properties", {}).items():
            if k in value: _validate(s, value[k], path + "." + k)
    elif typ == "string" and not isinstance(value, str): raise ValueError(path + " must be string")
    elif typ == "integer" and (not isinstance(value, int) or isinstance(value, bool)): raise ValueError(path + " must be integer")

def _calculator(a):
    node = ast.parse(a["expression"], mode="eval")
    allowed = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod, ast.USub, ast.UAdd, ast.Constant)
    if any(not isinstance(n, allowed) for n in ast.walk(node)): raise ValueError("only arithmetic is allowed")
    return str(eval(compile(node, "<calculator>", "eval"), {"__builtins__": {}}, {}))

def build_default_registry(workspace, enable_shell=False):
    r = ToolRegistry(); os.makedirs(workspace, exist_ok=True)
    r.register(ToolDefinition("calculator", "安全计算算术表达式", {"type":"object","properties":{"expression":{"type":"string"}},"required":["expression"],"additionalProperties":False}, _calculator))
    def read(a):
        p = _safe_path(workspace, a["path"]); return open(p, "r", encoding="utf-8").read()
    def write(a):
        p = _safe_path(workspace, a["path"]); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, "w", encoding="utf-8").write(a["content"]); return "written: " + a["path"]
    r.register(ToolDefinition("read_file", "读取 workspace 内文件", {"type":"object","properties":{"path":{"type":"string"}},"required":["path"],"additionalProperties":False}, read))
    r.register(ToolDefinition("write_file", "写入 workspace 内文件", {"type":"object","properties":{"path":{"type":"string"},"content":{"type":"string"}},"required":["path","content"],"additionalProperties":False}, write))
    def http_get(a):
        if not a["url"].startswith(("http://", "https://")): raise ValueError("only http/https")
        with urllib.request.urlopen(a["url"], timeout=10) as x: return x.read(20000).decode("utf-8", "replace")
    r.register(ToolDefinition("http_get", "读取公开 HTTP/HTTPS 页面前 20000 字符", {"type":"object","properties":{"url":{"type":"string"}},"required":["url"],"additionalProperties":False}, http_get))
    return r

def _safe_path(root, path):
    root = os.path.abspath(root); p = os.path.abspath(os.path.join(root, path))
    if os.path.commonprefix([root + os.sep, p + os.sep]) != root + os.sep: raise ValueError("path escapes workspace")
    return p
