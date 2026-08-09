[**开始使用**](./getting-started.md) > **安装** > **uv** _(当前)_

---

# 使用 uv 安装 GBabelDocUI

本页安装的是 GBabelDocUI。项目已经内置所需且经过校验的 `pdf2zh-next 2.9.0` 运行时子集，不要另行安装或使用上游 `pdf2zh_next` 命令替代 `gbabeldocui`。

## 环境要求

- Python 3.10–3.13
- Git
- [`uv`](https://docs.astral.sh/uv/getting-started/installation/)

## 安装并运行

```bash
git clone https://github.com/SocialYjj/GBabelDocUI.git
cd GBabelDocUI
uv sync --frozen
```

本机使用明文 HTTP 时：

=== "Linux 和 macOS"

    ```bash
    export GBABELDOCUI_COOKIE_SECURE=false
    uv run gbabeldocui
    ```

=== "Windows PowerShell"

    ```powershell
    $env:GBABELDOCUI_COOKIE_SECURE = "false"
    uv run gbabeldocui
    ```

打开 `http://127.0.0.1:7860/login.html`。

公开部署时保持 `GBABELDOCUI_COOKIE_SECURE=true`，使用 HTTPS 反向代理，并确保每个数据目录只运行一个进程和一个副本。

## 开发环境

```bash
uv sync --dev --frozen
uv run pytest -q
uv run ruff check gbabeldocui tests
uv run ruff format --check gbabeldocui tests
```
