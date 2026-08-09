# GBabelDocUI

GBabelDocUI 是面向自托管场景的多用户 PDF 翻译 Web UI，使用 FastAPI 提供认证、配置、任务、文件和历史记录接口，翻译核心为 BabelDOC。

本项目基于 [eaiu/GBabelDocUI](https://github.com/eaiu/GBabelDocUI) 修改，并内置经官方 PyPI wheel 校验的 `pdf2zh-next 2.9.0` 运行时子集。内置范围仅包括配置模型、高阶翻译接口、翻译器和异步桥接；不包含上游 CLI、Gradio GUI 或 HTTP API。来源、校验值和修改边界见 [`NOTICE`](NOTICE) 与[内置运行时来源说明](https://github.com/SocialYjj/GBabelDocUI/blob/main/gbabeldocui/_vendor/pdf2zh_next/UPSTREAM.md)。

## 当前能力

- 管理员和普通用户隔离，支持受控注册与用户管理。
- `HttpOnly` Cookie 会话、`SameSite=Strict`、CSRF 校验、会话上限和登录限流。
- PDF 内容、页数、页码范围、请求体、并发任务和用户存储配额校验。
- 用户设置、任务状态和历史记录使用 SQLite/JSON 持久化；浏览器不会收到已保存的 API 密钥。
- 上传取消、任务失败、超时、删除和服务重启均执行明确的状态与文件收尾。
- 完成、失败和取消任务默认保留 90 天；升级后默认等待 7 天再开始自动清理。
- 单实例数据目录锁，禁止多个进程或副本共享同一个 `data/` 目录。
- Docker 镜像使用固定基础镜像摘要、非 root 用户和多阶段构建；Compose 默认仅绑定本机地址并收紧容器权限。

## 本地启动

需要 Python 3.10–3.13 和 [uv](https://docs.astral.sh/uv/)。

```bash
git clone https://github.com/SocialYjj/GBabelDocUI.git
cd GBabelDocUI
uv sync --dev --frozen
```

Linux/macOS 本地明文 HTTP：

```bash
export GBABELDOCUI_COOKIE_SECURE=false
uv run gbabeldocui
```

Windows PowerShell 本地明文 HTTP：

```powershell
$env:GBABELDOCUI_COOKIE_SECURE = "false"
uv run gbabeldocui
```

默认监听 `0.0.0.0:7860`。公开部署必须通过 HTTPS 反向代理，并保持 `GBABELDOCUI_COOKIE_SECURE=true`。不要使用多个 Uvicorn worker，也不要启动多个共享同一数据目录的应用副本。

首次管理员初始化仅允许来自回环地址的请求。必须远程初始化时，启动前设置一次性高强度 `GBABELDOCUI_SETUP_TOKEN`，完成初始化后移除该变量并重启服务。

## Docker Compose

Linux 首次使用绑定目录前，应让镜像内 UID/GID `10001:10001` 可以写入：

```bash
mkdir -p data
sudo chown -R 10001:10001 data
docker compose up -d --build
```

Compose 默认发布到 `http://127.0.0.1:7860`，并显式设置 `GBABELDOCUI_COOKIE_SECURE=false` 以支持本机 HTTP。通过 HTTPS 反向代理公开服务时至少设置：

```bash
export GBABELDOCUI_COOKIE_SECURE=true
export GBABELDOCUI_SETUP_TOKEN='replace-with-a-long-random-value'
docker compose up -d
```

Compose 已启用非 root 用户、只读根文件系统、`no-new-privileges`、能力删除、PID/CPU/内存限制、临时文件系统和日志轮换。持久数据写入 `./data`，BabelDOC 模型及字体缓存写入命名卷 `/cache`。

## 主要环境变量

| 变量 | 默认值 | 说明 |
| --- | ---: | --- |
| `PORT` | `7860` | 服务端口 |
| `GBABELDOCUI_DATA_DIR` | `./data` | 运行数据目录 |
| `GBABELDOCUI_COOKIE_SECURE` | `true` | HTTPS 部署保持 `true`；仅本地 HTTP 设为 `false` |
| `GBABELDOCUI_SETUP_TOKEN` | 空 | 远程首次初始化所需的一次性令牌 |
| `GBABELDOCUI_ALLOWED_ORIGINS` | 空 | 独立可信前端来源，多个值用逗号分隔 |
| `GBABELDOCUI_MAX_UPLOAD_BYTES` | `52428800` | 单个上传请求上限 |
| `GBABELDOCUI_MAX_USER_STORAGE_BYTES` | `2147483648` | 单用户存储上限 |
| `GBABELDOCUI_MAX_ACTIVE_TASKS_PER_USER` | `2` | 单用户活动任务上限 |
| `GBABELDOCUI_MAX_ACTIVE_TASKS_GLOBAL` | `8` | 全局活动任务上限 |
| `GBABELDOCUI_MAX_SESSIONS_PER_USER` | `10` | 单用户有效会话上限 |
| `GBABELDOCUI_TRANSLATION_TIMEOUT_SECONDS` | `7200` | 单任务运行时限 |
| `GBABELDOCUI_MAX_USERS` | `1000` | 账户总数上限 |
| `GBABELDOCUI_AUTH_ATTEMPT_LIMIT` | `5` | 登录/注册失败窗口内次数上限 |
| `GBABELDOCUI_AUTH_ATTEMPT_WINDOW_SECONDS` | `300` | 认证限流窗口秒数 |
| `GBABELDOCUI_ORPHAN_UPLOAD_TTL_SECONDS` | `604800` | 未关联上传文件保留时间 |
| `GBABELDOCUI_TASK_RETENTION_DAYS` | `90` | 终态任务及文件保留天数 |
| `GBABELDOCUI_RETENTION_GRACE_DAYS` | `7` | 升级后首次自动清理宽限天数 |
| `GBABELDOCUI_ALLOW_PRIVATE_ENDPOINTS` | `false` | 是否允许管理员配置私网翻译端点 |

## 数据目录

```text
data/
├── users.db
├── .gbabeldocui-instance.lock
├── .gbabeldocui-retention-v1
└── users/
    └── {username}/
        ├── settings.json
        ├── history.json      # 仅用于旧版本历史的一次性导入
        ├── uploads/
        └── outputs/
```

SQLite 是任务运行状态和历史记录的唯一事实源。旧 `history.json` 只读取并记账导入一次，不再由服务持续重写，也不会在迁移时删除。`data/` 可能包含账户数据库、API 密钥、上传文件和翻译结果，禁止提交、打包或公开备份。

## 镜像发布

GitHub Actions 会在 Pull Request、`main` 推送和手动运行时执行测试、发行包审计、严格文档构建、镜像构建和 Trivy 门禁，但不会自动发布。只有形如 `v<项目版本>`、指向 `main` 历史提交且与 `pyproject.toml` 版本完全一致的标签才会发布 GHCR 镜像。发布镜像附带 SBOM、BuildKit 来源证明和 GitHub OIDC Cosign 签名。

当前工作流构建 `linux/amd64`。ARM 环境应在目标机器使用 Compose 本地构建。

## 许可证与对应源码

本项目及内置的上游运行时子集遵循 [`AGPL-3.0`](LICENSE)。公开网络部署时，应向使用者提供与实际部署版本对应的完整源码；Web UI 页脚已提供本仓库源码与许可证入口。
