import json, time, urllib.request

class ModelResponse:
    def __init__(self, content=None, tool_calls=None): self.content=content or ""; self.tool_calls=tool_calls or []

class AgentConfig:
    def __init__(self, name="main", system_prompt="You are a helpful agent.", allowed_tools=None, max_rounds=8, max_depth=2, subagents=None):
        self.name, self.system_prompt, self.allowed_tools = name, system_prompt, allowed_tools
        self.max_rounds, self.max_depth, self.subagents = max_rounds, max_depth, subagents or {}

class OpenAIModel:
    def __init__(self, base_url, api_key, model, timeout=60): self.url=base_url.rstrip("/")+"/chat/completions"; self.key=api_key; self.model=model; self.timeout=timeout
    def complete(self, messages, tools):
        body=json.dumps({"model":self.model,"messages":messages,"tools":tools,"tool_choice":"auto"}).encode("utf-8")
        req=urllib.request.Request(self.url, body, {"Content-Type":"application/json", "Authorization":"Bearer "+self.key})
        with urllib.request.urlopen(req, timeout=self.timeout) as x: data=json.loads(x.read().decode("utf-8"))
        message=data["choices"][0]["message"]; calls=[]
        for call in message.get("tool_calls", []):
            fn=call.get("function", {})
            try: args=json.loads(fn.get("arguments", "{}"))
            except ValueError: args={}
            calls.append({"id":call.get("id", ""),"name":fn.get("name", ""),"arguments":args})
        return ModelResponse(message.get("content") or "", calls)

class AgentRuntime:
    def __init__(self, registry, model, audit=None): self.registry=registry; self.model=model; self.audit=audit or []
    def run(self, task, config, depth=0):
        if depth > config.max_depth: return "subagent depth limit reached"
        messages=[{"role":"system","content":config.system_prompt},{"role":"user","content":task}]
        for _ in range(config.max_rounds):
            response=self.model.complete(messages, self._schemas(config))
            if response.tool_calls:
                c=response.tool_calls[0]; raw=json.dumps({"type":"tool_call","name":c["name"],"arguments":c["arguments"],"id":c.get("id","")})
            else: raw=response.content
            data=self._parse(raw); self.audit.append({"agent":config.name,"response":data})
            if data.get("type") == "final": return data.get("content", "")
            if data.get("type") != "tool_call": return raw
            name=data.get("name"); args=data.get("arguments", {})
            if config.allowed_tools is not None and name not in config.allowed_tools: result="permission denied: "+name
            elif name == "delegate": result=self._delegate(args, config, depth)
            else:
                try: result=self.registry.execute(name, args)
                except Exception as e: result="tool error: "+str(e)
            messages.append({"role":"assistant","content":raw}); messages.append({"role":"tool","tool_call_id":data.get("id",""),"name":name,"content":str(result)})
        return "max rounds reached"
    def _schemas(self, config):
        schemas = self.registry.schemas(config.allowed_tools)
        if config.subagents and (config.allowed_tools is None or "delegate" in config.allowed_tools):
            schemas.append({"type":"function", "function":{"name":"delegate", "description":"将任务委派给指定子 Agent", "parameters":{"type":"object","properties":{"agent":{"type":"string"},"task":{"type":"string"}},"required":["agent","task"],"additionalProperties":False}}})
        return schemas

    def _delegate(self, args, parent, depth):
        spec=parent.subagents.get(args.get("agent"));
        if not spec: return "unknown subagent: "+str(args.get("agent"))
        return self.run(args.get("task", ""), spec, depth+1)
    def _parse(self, raw):
        text=raw.strip()
        if text.startswith("```"):
            text=text.split("\n",1)[1].rsplit("```",1)[0].strip()
        try: return json.loads(text)
        except ValueError: return {"type":"final","content":raw}

class ScriptedModel:
    def __init__(self, responses): self.responses=list(responses); self.calls=0
    def complete(self, messages, tools):
        x=self.responses[min(self.calls, len(self.responses)-1)]; self.calls+=1; return ModelResponse(x)
