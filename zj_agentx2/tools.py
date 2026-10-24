import ast, json, os, urllib.request, datetime, uuid, glob, platform

class ToolDefinition:
    def __init__(self, name, description, schema, handler, category="utility", risk="low"):
        self.name, self.description, self.schema, self.handler, self.category, self.risk = name, description, schema, handler, category, risk

class ToolRegistry:
    def __init__(self): self._tools = {}
    def register(self, tool): self._tools[tool.name] = tool
    def get(self, name): return self._tools.get(name)
    def schemas(self, allowed=None):
        names = allowed if allowed is not None else self._tools.keys()
        return [{"type":"function", "function":{"name":t.name,"description":t.description,"parameters":t.schema}, "x-category":t.category, "x-risk":t.risk} for n in names if (t:=self.get(n))]
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
        p = _safe_path(workspace, a["path"]); os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f: f.write(a["content"])
        return "written: " + a["path"]
    r.register(ToolDefinition("read_file", "读取 workspace 内文件", {"type":"object","properties":{"path":{"type":"string"}},"required":["path"],"additionalProperties":False}, read))
    r.register(ToolDefinition("write_file", "写入 workspace 内文件", {"type":"object","properties":{"path":{"type":"string"},"content":{"type":"string"}},"required":["path","content"],"additionalProperties":False}, write))
    def http_get(a):
        if not a["url"].startswith(("http://", "https://")): raise ValueError("only http/https")
        with urllib.request.urlopen(a["url"], timeout=10) as x: return x.read(20000).decode("utf-8", "replace")
    r.register(ToolDefinition("http_get", "读取公开 HTTP/HTTPS 页面前 20000 字符", {"type":"object","properties":{"url":{"type":"string"}},"required":["url"],"additionalProperties":False}, http_get))
    r.register(ToolDefinition("current_time", "获取当前 UTC 时间", {"type":"object","properties":{},"additionalProperties":False}, lambda a: datetime.datetime.utcnow().isoformat() + "Z"))
    r.register(ToolDefinition("uuid", "生成 UUID", {"type":"object","properties":{},"additionalProperties":False}, lambda a: str(uuid.uuid4())))
    r.register(ToolDefinition("json_format", "格式化 JSON", {"type":"object","properties":{"text":{"type":"string"}},"required":["text"],"additionalProperties":False}, lambda a: json.dumps(json.loads(a["text"]),ensure_ascii=False,indent=2,sort_keys=True)))
    r.register(ToolDefinition("text_stats", "统计文本", {"type":"object","properties":{"text":{"type":"string"}},"required":["text"],"additionalProperties":False}, lambda a: json.dumps({"characters":len(a["text"]),"lines":len(a["text"].splitlines()),"words":len(a["text"].split())})))
    r.register(ToolDefinition("list_dir", "列出 workspace 目录", {"type":"object","properties":{"path":{"type":"string"}},"additionalProperties":False}, lambda a: json.dumps(sorted(os.listdir(_safe_path(workspace,a.get("path",""))))), "filesystem", "medium"))
    def find(a):
        base=os.path.abspath(workspace); root=_safe_path(workspace,a.get("path","")); return json.dumps([os.path.relpath(x,workspace) for x in glob.glob(os.path.join(root,a["pattern"]),recursive=True) if os.path.commonprefix([os.path.abspath(x),base+os.sep])==base+os.sep])
    r.register(ToolDefinition("find_files", "按 glob 搜索 workspace 文件", {"type":"object","properties":{"pattern":{"type":"string"},"path":{"type":"string"}},"required":["pattern"],"additionalProperties":False}, find, "filesystem", "medium"))
    r.register(ToolDefinition("system_info", "返回脱敏系统信息", {"type":"object","properties":{},"additionalProperties":False}, lambda a: json.dumps({"platform":platform.system(),"python":platform.python_version()})))
    return r

def _safe_path(root, path):
    root = os.path.abspath(root); p = os.path.abspath(os.path.join(root, path))
    if os.path.commonprefix([root + os.sep, p + os.sep]) != root + os.sep: raise ValueError("path escapes workspace")
    return p
