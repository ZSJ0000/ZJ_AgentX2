# 一键部署

## Linux

在项目目录执行：

```sh
sh deploy_linux.sh
```

脚本会创建项目目录内的 `.venv`、复制 `config.example.json` 为 `config.json`、创建 `workspace` 并运行测试。

启动：

```sh
sh start_linux.sh "介绍当前平台能力"
```

## Windows 7 / Windows

双击或在 CMD 执行：

```bat
deploy_windows.bat
```

启动：

```bat
start_windows.bat "介绍当前平台能力"
```

## 通用 Python

```bat
python deploy.py
python deploy.py --no-venv
python deploy.py --skip-tests
python deploy.py --start --task "计算 12*8"
```

部署程序不会覆盖已有 `config.json`，配置和虚拟环境都放在项目目录，不写入系统环境变量。Windows 7 使用 Python 3.8 时，如果 `venv` 创建失败，可使用 `--no-venv`，并确保当前 Python 已安装项目需要的依赖。
