import json, time, urllib.request
from .platform import model_context

class ModelResponse:
    def __init__(self, content=None, tool_calls=None): self.content=content or ""; self.tool_calls=tool_calls or []

class AgentConfig:
    def __init__(self, name="main", system_prompt="You are a helpful agent.", allowed_tools=None, max_rounds=8, max_depth=2, subagents=None, subagent_policy="prefer_when_complex"):
        self.name, self.system_prompt, self.allowed_tools = name, system_prompt, allowed_tools
        self.max_rounds, self.max_depth, self.subagents, self.subagent_policy = max_rounds, max_depth, subagents or {}, subagent_policy

class OpenAIModel:
    def __init__(self, base_url, api_key, model, timeout=60, stream=False, on_token=None):
        self.url=base_url.rstrip("/")+"/chat/completions"; self.key=api_key; self.model=model; self.timeout=timeout
        self.stream=bool(stream); self.on_token=on_token
    def _response(self, data):
        message=data["choices"][0].get("message", {}); calls=[]
        for call in message.get("tool_calls", []):
            fn=call.get("function", {})
            try: args=json.loads(fn.get("arguments", "{}"))
            except ValueError: args={}
            calls.append({"id":call.get("id", ""),"name":fn.get("name", ""),"arguments":args})
        return ModelResponse(message.get("content") or "", calls)
    def _complete_stream(self, response):
        content=[]; calls={}
        for raw in response:
            line=raw.decode("utf-8", "replace").strip()
            if not line or line.startswith(":"): continue
            if line.startswith("data:"): line=line[5:].strip()
            if line == "[DONE]": break
            try: chunk=json.loads(line)
            except ValueError: continue
            choice=(chunk.get("choices") or [{}])[0]; delta=choice.get("delta") or {}
            text=delta.get("content") or ""
            if text:
                content.append(text)
                if self.on_token: self.on_token(text)
            for part in delta.get("tool_calls") or []:
                i=part.get("index",0); item=calls.setdefault(i,{"id":"","name":"","arguments":""})
                item["id"] += part.get("id") or ""; fn=part.get("function") or {}
                item["name"] += fn.get("name") or ""; item["arguments"] += fn.get("arguments") or ""
        parsed=[]
        for item in calls.values():
            try: args=json.loads(item["arguments"] or "{}")
            except ValueError: args={}
            parsed.append({"id":item["id"],"name":item["name"],"arguments":args})
        return ModelResponse("".join(content), parsed)
    def complete(self, messages, tools):
        body={"model":self.model,"messages":messages,"tools":tools,"tool_choice":"auto"}
        if self.stream: body["stream"]=True
        req=urllib.request.Request(self.url,json.dumps(body).encode("utf-8"),{"Content-Type":"application/json","Authorization":"Bearer "+self.key})
        with urllib.request.urlopen(req, timeout=self.timeout) as x:
            return self._complete_stream(x) if self.stream else self._response(json.loads(x.read().decode("utf-8")))

class AgentRuntime:
    def __init__(self, registry, model, audit=None, platform_context=None): self.registry=registry; self.model=model; self.audit=audit or []; self.platform_context=platform_context or model_context(); self._stop_requested=False
    def request_stop(self): self._stop_requested=True
    def run_long_task(self, task, config, stop_event=None, max_cycles=1000, depth=0):
        import threading
        event=stop_event or threading.Event(); self._stop_requested=False; results=[]; cycles=0
        while cycles < max_cycles and not event.is_set() and not self._stop_requested:
            cycles += 1
            result=self.run(task if cycles == 1 else '继续执行上一个长任务；完成后继续，不要主动结束。', config, depth=depth, long_mode=True, stop_event=event)
            results.append(result)
        reason='user_or_tool_stop' if event.is_set() or self._stop_requested else 'safety_limit'
        self.audit.append({'agent':config.name,'long_task':True,'cycles':cycles,'stop_reason':reason})
        return {'result':results[-1] if results else '', 'results':results, 'cycles':cycles, 'stop_reason':reason}
    def _stop_tool(self,args,event):
        if args.get('stop',False):
            if event: event.set()
            self._stop_requested=True
            return 'long task stop requested: '+str(args.get('reason','model requested stop'))
        return 'stop remains false; continue'

    def run(self, task, config, depth=0, long_mode=False, stop_event=None):
        if depth > config.max_depth: return "subagent depth limit reached"
        messages=[{"role":"system","content":config.system_prompt + "\n\n" + self.platform_context},{"role":"user","content":task}]
        event=stop_event
        for _ in range(config.max_rounds):
            if event is not None and event.is_set(): return "stopped by user"
            self._schema_long_mode=long_mode
            response=self.model.complete(messages, self._schemas(config))
            if response.tool_calls:
                c=response.tool_calls[0]; raw=json.dumps({"type":"tool_call","name":c["name"],"arguments":c["arguments"],"id":c.get("id","")})
            else: raw=response.content
            data=self._parse(raw); self.audit.append({"agent":config.name,"response":data})
            if data.get("type") == "final":
                if long_mode and not (event is not None and event.is_set()) and not self._stop_requested:
                    messages.append({"role":"assistant","content":data.get("content","")}); messages.append({"role":"user","content":"继续执行。只有调用 long_task_stop 且 stop=true，或用户停止，才能结束。"}); continue
                return data.get("content", "")
            if data.get("type") != "tool_call": return raw
            name=data.get("name"); args=data.get("arguments", {})
            if config.allowed_tools is not None and name not in config.allowed_tools and not (long_mode and name == "long_task_stop"): result="permission denied: "+name
            elif name == "long_task_stop": result=self._stop_tool(args,event)
            elif name == "delegate": result=self._delegate(args, config, depth)
            else:
                try: result=self.registry.execute(name, args)
                except Exception as e: result="tool error: "+str(e)
            messages.append({"role":"assistant","content":raw}); messages.append({"role":"tool","tool_call_id":data.get("id",""),"name":name,"content":str(result)})
        return "max rounds reached"
    def _schemas(self, config):
        schemas = self.registry.schemas(config.allowed_tools)
        if getattr(self, "_schema_long_mode", False): schemas.append({"type":"function","function":{"name":"long_task_stop","description":"停止长任务","parameters":{"type":"object","properties":{"stop":{"type":"boolean"},"reason":{"type":"string"}},"required":["stop"],"additionalProperties":False}}})
        if config.subagents and (config.allowed_tools is None or "delegate" in config.allowed_tools):
            schemas.append({"type":"function", "function":{"name":"delegate", "description":"将复杂、独立或需要复核的子任务委派给指定子 Agent。可用名称: " + ", ".join(config.subagents.keys()), "parameters":{"type":"object","properties":{"agent":{"type":"string","enum":list(config.subagents.keys())},"task":{"type":"string"}},"required":["agent","task"],"additionalProperties":False}}})
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
        self.last_messages=messages
        x=self.responses[min(self.calls, len(self.responses)-1)]; self.calls+=1; return ModelResponse(x)
