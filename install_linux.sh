#!/bin/sh
set -e
REPO="https://github.com/ZSJ0000/ZJ_AgentX2.git"; DIR="${ZJ_AGENTX2_DIR:-$HOME/ZJ_AgentX2}"; NO_VENV=""; SKIP_TESTS=""; START=""
while [ "$#" -gt 0 ]; do case "$1" in --dir) DIR="$2"; shift 2;; --no-venv) NO_VENV="--no-venv"; shift;; --skip-tests) SKIP_TESTS="--skip-tests"; shift;; --start) START="--start"; shift;; *) echo "Unknown option: $1"; exit 2;; esac; done
if [ -e "$DIR/.git" ]; then echo "[install] update existing: $DIR"; git -C "$DIR" pull --ff-only; elif command -v git >/dev/null 2>&1; then echo "[install] clone: $DIR"; mkdir -p "$(dirname "$DIR")"; git clone "$REPO" "$DIR"; else echo "[install] git is required; install git and retry"; exit 3; fi
cd "$DIR"; python3 deploy.py $NO_VENV $SKIP_TESTS $START; printf '%s\n' "[install] complete: $DIR" "[install] edit: $DIR/config.json" "[install] start: sh $DIR/start_linux.sh"
