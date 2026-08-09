# GBabelDocUI

GBabelDocUI 是基于 BabelDOC 的自托管多用户 PDF 翻译 Web UI。

本项目基于 [`eaiu/GBabelDocUI`](https://github.com/eaiu/GBabelDocUI) 修改，并内置经校验的 `pdf2zh-next 2.9.0` 运行时子集。内置内容仅包含本 Web UI 使用的配置模型、高阶翻译入口、翻译器和异步桥接，不包含上游命令行工具、Gradio 界面或 HTTP API。

## 主要能力

- 管理员和普通用户账户，配置、文件、任务与历史记录按用户隔离。
- `HttpOnly` Cookie 会话、CSRF 防护、登录限流和单用户会话上限。
- PDF 内容、大小、页数、页码范围、存储配额与任务并发校验。
- Web 设置页支持 OpenAI、Azure OpenAI 和 Google Gemini。
- SQLite 持久化任务状态与历史记录，并提供明确的保留期和清理机制。
- 单实例 Docker Compose 部署，使用非 root 用户和只读根文件系统。

## 快速开始

### Docker Compose

```bash
git clone https://github.com/SocialYjj/GBabelDocUI.git
cd GBabelDocUI
mkdir -p data
sudo chown -R 10001:10001 data  # 仅 Linux 绑定目录需要
docker compose up -d --build
```

打开 `http://127.0.0.1:7860/login.html`。Compose 默认仅绑定回环地址，并为本机 HTTP 设置 `GBABELDOCUI_COOKIE_SECURE=false`。

### uv

需要 Python 3.10–3.13 和 [`uv`](https://docs.astral.sh/uv/)。

```bash
git clone https://github.com/SocialYjj/GBabelDocUI.git
cd GBabelDocUI
uv sync --frozen
export GBABELDOCUI_COOKIE_SECURE=false
uv run gbabeldocui
```

Windows PowerShell 将 `export` 命令替换为：

```powershell
$env:GBABELDOCUI_COOKIE_SECURE = "false"
```

## 部署边界

- 公开访问必须使用 HTTPS 反向代理，并保持 `GBABELDOCUI_COOKIE_SECURE=true`。
- 首个管理员只允许通过回环请求创建。必须远程初始化时，设置一次性高强度 `GBABELDOCUI_SETUP_TOKEN`，完成后立即移除并重启服务。
- 每个数据目录只运行一个应用进程和一个副本；不得让多个 Uvicorn worker 或多个副本共享同一 `data/` 目录。
- `data/` 可能包含账户、API 密钥、上传 PDF 和翻译结果，禁止提交、打包或公开。
- Web UI 不提供内置上游命令行工具、Gradio 界面或 HTTP API。

## 文档

- [Docker 安装](./getting-started/INSTALLATION_docker.md)
- [uv 安装](./getting-started/INSTALLATION_uv.md)
- [Web UI 使用](./getting-started/USAGE_webui.md)
- [高级参考](./advanced/advanced.md)
- [翻译服务](./advanced/Documentation-of-Translation-Services.md)

## 来源与许可证

GBabelDocUI 及内置的上游运行时子集按 [AGPL-3.0](https://github.com/SocialYjj/GBabelDocUI/blob/main/LICENSE) 发布。来源、校验值和修改边界见 [`NOTICE`](https://github.com/SocialYjj/GBabelDocUI/blob/main/NOTICE) 与[内置运行时来源说明](https://github.com/SocialYjj/GBabelDocUI/blob/main/gbabeldocui/_vendor/pdf2zh_next/UPSTREAM.md)。
