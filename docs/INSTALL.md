# 仓库外一键安装

## Linux

不需要先手动下载仓库，在终端执行：

```sh
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ZSJ0000/ZJ_AgentX2/master/install_linux.sh)"
```

如果没有 curl：

```sh
wget -qO- https://raw.githubusercontent.com/ZSJ0000/ZJ_AgentX2/master/install_linux.sh | sh
```

默认安装到：

```text
~/ZJ_AgentX2
```

指定目录：

```sh
ZJ_AGENTX2_DIR=/opt/ZJ_AgentX2 sh -c "$(curl -fsSL https://raw.githubusercontent.com/ZSJ0000/ZJ_AgentX2/master/install_linux.sh)"
```

## Windows 7 / Windows CMD

Windows 7 CMD 不能可靠地使用 curl 下载脚本，推荐先下载仓库 ZIP 或安装 Git，然后执行仓库内的：

```bat
install_windows.bat
```

如果已经安装 Git，可以在 CMD 执行：

```bat
git clone https://github.com/ZSJ0000/ZJ_AgentX2.git "%USERPROFILE%\ZJ_AgentX2" && "%USERPROFILE%\ZJ_AgentX2\install_windows.bat" --no-venv
```

指定目录：

```bat
install_windows.bat --dir D:\ZJ_AgentX2 --no-venv
```

脚本完成后会创建或保留项目目录内的 `config.json`，创建 `workspace`，运行测试，并提示启动命令。已有配置不会覆盖。
