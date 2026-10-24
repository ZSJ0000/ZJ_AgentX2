#!/bin/sh
set -e
cd "$(dirname "$0")"
if [ -x .venv/bin/python ]; then exec .venv/bin/python -m zj_agentx2 --config config.json --task "${1:-请介绍当前平台能力}"; fi
exec python3 -m zj_agentx2 --config config.json --task "${1:-请介绍当前平台能力}"
