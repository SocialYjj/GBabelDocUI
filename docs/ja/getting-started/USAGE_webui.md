[**開始**](./getting-started.md) > **インストール** > **WebUI** _(現在)_

---

### Webui で GBabelDocUI を使用する

#### WebUI ページを開く方法：

WebUI インターフェースを開く方法はいくつかあります。**Windows** を使用している場合は、[この記事](./INSTALLATION_winexe.md) を参照してください。

1. Python がインストールされていること（3.10 <= バージョン <= 3.12）

2. パッケージをインストール：

3. ブラウザで使用開始：

    ```bash
    gbabeldocui
    ```

4. ブラウザが自動的に起動しない場合、次の URL にアクセス：

    ```bash
    http://localhost:7860/
    ```

    PDF ファイルをウィンドウにドロップし、`Translate` をクリック。

5. GBabelDocUI を docker でデプロイし、GBabelDocUI のバックエンド LLM として ollama を使用している場合、「Ollama host」に次のように入力：

   ```bash
   http://host.docker.internal:11434
   ```

> **セキュリティに関する注意:** Ollama はサーバー側のサービスで、管理者のみ利用できます。プライベートエンドポイント `http://host.docker.internal:11434` はデフォルトで拒否されます。信頼できる環境でのみ、コンテナの環境変数に `GBABELDOCUI_ALLOW_PRIVATE_ENDPOINTS=true` を設定してください。この設定は SSRF 防御を緩和するため、信頼できないユーザーが GBabelDocUI にアクセスできる環境では有効にしないでください。

<!-- <img src="./../../images/gui.gif" width="500"/> -->
<img src='./../../images/gui.gif' width="500"/>
### Configure the translation

Use the GBabelDocUI settings page to choose the translation service, source and target languages, PDF outputs, page range and advanced options. The selected settings are saved per user and are snapshotted when a task starts.

When running the Docker container, keep `./data` mounted to `/app/data`. The default Compose deployment listens on `127.0.0.1:7860`; use an HTTPS reverse proxy for public access. The translation executor is designed for one application process and one shared data directory.
## Preview## プレビュー

<img src="./../../images/before.png" width="500"/>
<img src="./../../images/after.png" width="500"/>

<div align="right"> 
<h6><small>このページの一部のコンテンツは GPT によって翻訳されており、エラーが含まれている可能性があります。</small></h6>