# uv で GBabelDocUI をインストール

必要な検証済み pdf2zh-next ランタイムは同梱済みです。上流 CLI を `gbabeldocui` の代わりに使用しないでください。

## 必要な環境

- Python 3.10–3.13
- Git
- [uv](https://docs.astral.sh/uv/getting-started/installation/)

## インストールと実行

```bash
git clone https://github.com/SocialYjj/GBabelDocUI.git
cd GBabelDocUI
uv sync --frozen
```

=== "Linux/macOS"

    ```bash
    export GBABELDOCUI_COOKIE_SECURE=false
    uv run gbabeldocui
    ```

=== "Windows PowerShell"

    ```powershell
    $env:GBABELDOCUI_COOKIE_SECURE = "false"
    uv run gbabeldocui
    ```

起動後に `http://127.0.0.1:7860/login.html` を開きます。

公開環境では Secure Cookie を維持し、HTTPS とデータディレクトリごとに 1 インスタンスを使用します。

## 開発環境

```bash
uv sync --dev --frozen
uv run pytest -q
uv run ruff check gbabeldocui tests
uv run ruff format --check gbabeldocui tests
```
