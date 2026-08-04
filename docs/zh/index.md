# GBabelDocUI

基于官方 [`pdf2zh-next`](https://github.com/PDFMathTranslate-next/PDFMathTranslate-next) 运行时的多用户 PDF 翻译 Web UI 适配层。

本项目基于 [`eaiu/GBabelDocUI`](https://github.com/eaiu/GBabelDocUI) 修改，当前维护仓库为 [`SocialYjj/GBabelDocUI`](https://github.com/SocialYjj/GBabelDocUI)。核心翻译引擎由 [`BabelDOC`](https://github.com/funstory-ai/BabelDOC) 提供。

## 主要能力

- 多用户注册、登录、管理员和普通用户权限隔离。
- 用户配置、翻译历史、上传文件和输出文件持久化保存。
- PDF 上传校验、用户存储配额、翻译任务状态和任务恢复。
- 支持 OpenAI、硅基流动、Gemini、Ollama 等由官方运行时提供的翻译服务。
- 支持单语 PDF、双语 PDF、页面范围、术语提取和 BabelDOC 高级选项。

## Docker 部署

推荐在 Linux 或 VPS 上使用仓库根目录的 Compose 配置：

```bash
git clone https://github.com/SocialYjj/GBabelDocUI.git
cd GBabelDocUI
docker compose up -d --build
```

默认访问 `http://127.0.0.1:7860`。Compose 会将 `./data` 挂载到 `/app/data`，其中包含账户、配置、上传文件和翻译结果；该目录只保存在本地或 VPS，不得提交到公开仓库。

首次 GitHub Actions 发布完成后，也可以使用当前仓库的 amd64 GHCR 镜像：

```bash
docker pull ghcr.io/socialyjj/gbabeldocui:latest
docker run -d \
  --name gbabeldocui \
  --restart unless-stopped \
  -p 127.0.0.1:7860:7860 \
  -v "$(pwd)/data:/app/data" \
  ghcr.io/socialyjj/gbabeldocui:latest
```

公开访问时应配置 HTTPS 反向代理。翻译执行器按单进程设计，请保持一个 Uvicorn worker 和一个应用副本，不要让多个副本共享同一个 `data/` 目录。

## Web UI 使用

1. 打开 `/login.html`，首次运行时创建管理员账户。
2. 在“设置”页面填写翻译服务、模型、API Key、源语言、目标语言、PDF 输出和页面范围。
3. 在“上传”页面选择 PDF 并开始翻译；任务进度和历史记录会按当前用户隔离。
4. 翻译完成后下载单语或双语 PDF。API Key 等敏感设置只保存到本地 `data/`，不要导出或提交到 Git。

详细说明：

- [Docker 安装](./getting-started/INSTALLATION_docker.md)
- [Web UI 使用](./getting-started/USAGE_webui.md)
- [高级选项](./advanced/advanced.md)
- [翻译服务文档](./advanced/Documentation-of-Translation-Services.md)
- [支持的语言](./supported_languages.md)

## 本地开发

```bash
uv sync --dev --frozen
uv run pytest -q
uv run ruff check gbabeldocui tests
uv run ruff format --check gbabeldocui tests
```

前端直接使用仓库内的静态文件；真实部署和数据边界说明见根目录 [`README.md`](https://github.com/SocialYjj/GBabelDocUI/blob/main/README.md)、[`NOTICE`](https://github.com/SocialYjj/GBabelDocUI/blob/main/NOTICE) 和 [`docker-compose.yml`](https://github.com/SocialYjj/GBabelDocUI/blob/main/docker-compose.yml)。

## 来源与许可证

本项目遵循 [AGPL-3.0](https://github.com/SocialYjj/GBabelDocUI/blob/main/LICENSE)。第三方运行时、BabelDOC 和早期来源的修改范围见 [`NOTICE`](https://github.com/SocialYjj/GBabelDocUI/blob/main/NOTICE)。

问题反馈和代码贡献请提交到 [GitHub Issues](https://github.com/SocialYjj/GBabelDocUI/issues) 或 Pull Request；不要上传 `data/`、`yuan/`、数据库、密钥、PDF 和生成结果。
