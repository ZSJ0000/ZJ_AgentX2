import argparse, json, os
from .core import AgentConfig, AgentRuntime, OpenAIModel
from .tools import build_default_registry

def main():
    p=argparse.ArgumentParser(); p.add_argument("--config", default="config.json"); p.add_argument("--task", required=True); p.add_argument("--workspace"); a=p.parse_args()
    c=json.load(open(a.config, encoding="utf-8")); workspace=a.workspace or c.get("workspace", "workspace")
    registry=build_default_registry(workspace, c.get("enable_shell", False)); model=OpenAIModel(c["base_url"], c.get("api_key", ""), c["model"], c.get("timeout_seconds",60))
    cfg=AgentConfig(max_rounds=c.get("max_rounds",8), max_depth=c.get("max_depth",2), allowed_tools=["calculator","read_file","write_file","http_get"])
    print(AgentRuntime(registry, model).run(a.task, cfg))
if __name__ == "__main__": main()
