# GBabelDocUI

基于官方 [pdf2zh-next](https://github.com/PDFMathTranslate-next/PDFMathTranslate-next) 的多用户 Web UI 适配层。

本项目是基于 [eaiu/GBabelDocUI](https://github.com/eaiu/GBabelDocUI) 修改而来。**原作者**：eaiu。

当前仓库已经**不再内置本地 `pdf2zh_next` fork**，运行时直接依赖官方包：

- **官方运行时**: `pdf2zh-next`
- **核心引擎**: [BabelDOC](https://github.com/funstory-ai/BabelDOC)
- **本仓库职责**: 多用户认证、配置持久化、翻译历史、文件管理、Web UI

## 新增功能

### 全新 UI

- **现代化界面**: 简洁的设计风格
- **独立 Web 入口**: 直接运行 `gbabeldocui`
  ![mainPage](./static/mainPage.png)

### 用户系统

- **多用户支持**: 支持管理员和普通用户
- **首次设置向导**: 自动引导创建管理员账户
- **用户自助注册**: 管理员可控制是否允许新用户注册
- **JWT 认证**: 安全的 Token 认证机制
- **会话管理**: 登录状态持久化，支持过期自动清理

### 持久化用户配置

- **用户数据持久化**: 刷新网页后配置不会丢失
- **独立配置空间**: 每个用户拥有独立设置
- **配置导入/导出**: 一键导出为 JSON，支持跨用户复用

### 文件管理

- **翻译历史**: 查看所有翻译记录
- **文件下载**: 支持下载 Mono / Dual 版本
- **一键删除**: 删除历史记录及关联文件

## 本地启动

```bash
git clone https://github.com/SocialYjj/GBabelDocUI.git
cd GBabelDocUI
uv venv .venv
source .venv/bin/activate
uv sync --dev
gbabeldocui
```

默认监听：

- `http://127.0.0.1:7860`

可选环境变量：

```bash
export PORT=7860
export GBABELDOCUI_DATA_DIR=/absolute/path/to/data
# 仅在前后端跨域部署时设置，多个来源使用逗号分隔
export GBABELDOCUI_ALLOWED_ORIGINS=https://example.com
# 默认 50 MiB
export GBABELDOCUI_MAX_UPLOAD_BYTES=52428800
```

## Docker 部署

```yaml
version: '3.8'

services:
  gbabeldocui:
    build: .
    container_name: gbabeldocui
    ports:
      - "7860:7860"
    restart: unless-stopped
    volumes:
      - ./data:/app/data
```

### 使用 GitHub Container Registry 镜像

`.github/workflows/docker-publish.yml` 会在 `v*` 标签推送或手动运行时构建并发布镜像；Pull Request 只构建和扫描，不发布。发布后可直接使用：

```bash
docker pull ghcr.io/socialyjj/gbabeldocui:latest
docker run -d \
  --name gbabeldocui \
  --restart unless-stopped \
  -p 7860:7860 \
  -v "$(pwd)/data:/app/data" \
  ghcr.io/socialyjj/gbabeldocui:latest
```

工作流还会为版本标签生成版本号和提交短 SHA 标签。首次发布后，如果 GHCR 包不是公开的，需要在 GitHub 的 Package settings 中将其设置为 Public，VPS 才能免认证拉取；`data/` 仍只通过本地持久化卷挂载，不会进入镜像。

## 数据目录结构

```text
data/
├── users.db          # 用户认证数据库
└── users/
    └── {username}/
        ├── settings.json  # 用户配置
        ├── history.json   # 翻译历史
        ├── uploads/       # 上传的文件
        └── outputs/       # 翻译结果
```

`data/` 是运行时数据目录，包含数据库、上传文件、翻译结果、用户配置和可能的 API 密钥。该目录必须保留在本地或 VPS 持久化卷中，但被 `.gitignore` 和 `.dockerignore` 排除，不应提交到公开仓库。`yuan/` 仅作为本地来源对照目录，也不会进入本仓库。

## 说明

- 当前 WebUI 运行时会直接调用官方 `pdf2zh_next.high_level.do_translate_async_stream`
- 首次真实翻译时，BabelDOC 可能下载字体和模型资源，因此第一次会明显更慢
- 如果只想做 smoke test，建议使用简单英文 PDF，并在设置里关闭 `translate_tables`

## 来源与修改

- 来源、修改范围和第三方运行时说明见 [NOTICE](NOTICE)。
- 本项目没有把 `pdf2zh_next` 源码复制到仓库内，而是通过锁定的 `pdf2zh-next` 和 `BabelDOC` 依赖调用官方运行时。
- 本项目的修改集中在多用户认证、用户配置持久化、翻译历史、文件管理、Web UI 以及部署边界处理。

## License

本项目遵循 [AGPL-3.0 License](LICENSE)，与原项目保持一致。
