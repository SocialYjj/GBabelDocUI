# GBabelDocUI Web UI の使い方

サービスはブラウザーを自動的に開きません。起動後、ログインページを手動で開いてください。

## 必要な環境

- Python 3.10–3.13
- Git
- [uv](https://docs.astral.sh/uv/)

## リポジトリから実行

```bash
git clone https://github.com/SocialYjj/GBabelDocUI.git
cd GBabelDocUI
uv sync --frozen
```

ローカル HTTP では Cookie の Secure 属性を無効にします。

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

## 初回利用

1. ローカルのログインページから最初の管理者を作成します。
2. 設定で OpenAI、Azure OpenAI、Google Gemini のいずれかを構成します。
3. 言語、出力、ページ範囲、PDF オプションを選択します。
4. PDF をアップロードしてタスクを開始し、履歴から結果をダウンロードします。

保存した API キーはサーバー側に残ります。`data/` をコミットまたは公開しないでください。

コンテナでは Docker Compose の手順を使用してください。公開環境では HTTPS と、データディレクトリごとに 1 インスタンスが必要です。
