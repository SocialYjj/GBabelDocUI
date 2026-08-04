[**開始**](./getting-started.md) > **インストール** > **Docker** _(current)_

---

### GBabelDocUI を docker でインストール

#### Docker とは何ですか？

[Docker](https://docs.docker.com/get-started/docker-overview/) は、アプリケーションの開発、配布、実行のためのオープンプラットフォームです。Docker を使用すると、アプリケーションをインフラストラクチャから分離できるため、ソフトウェアを迅速に提供できます。Docker では、アプリケーションを管理するのと同じ方法でインフラストラクチャを管理できます。Docker のコード配布、テスト、デプロイの方法論を活用することで、コードを記述してから本番環境で実行するまでの遅延を大幅に削減できます。

#### インストール

<h4>1. Start the application with the repository Compose file:</h4>

```bash
docker compose up -d --build
```

> [!NOTE]
>
> The Compose file persists `./data` for accounts, settings, uploads and outputs. The default port binding is `127.0.0.1:7860`; put the service behind an HTTPS reverse proxy before exposing it publicly.
>
> After the first successful GitHub Actions publish, you can use the amd64 GHCR image instead:
>
> ```bash
> docker pull ghcr.io/socialyjj/gbabeldocui:latest
> docker run -d --name gbabeldocui --restart unless-stopped -p 127.0.0.1:7860:7860 -v "$(pwd)/data:/app/data" ghcr.io/socialyjj/gbabeldocui:latest
> ```
<h4>2. デフォルトのブラウザでこの URL を入力して WebUI ページを開きます：</h4>

```
http://localhost:7860/
```

> [!NOTE]
> WebUI の使用中に問題が発生した場合は、[使い方 --> WebUI](./USAGE_webui.md) を参照してください。

> [!NOTE]
> コマンドラインの使用中に問題が発生した場合は、[使い方 --> コマンドライン](./USAGE_commandline.md) を参照してください。
<!-- 
#### For docker deployment on cloud service:

<div>
<a href="https://www.heroku.com/deploy?template=https://github.com/GBabelDocUI/GBabelDocUI-next">
  <img src="https://www.herokucdn.com/deploy/button.svg" alt="Deploy" height="26"></a>
<a href="https://render.com/deploy">
  <img src="https://render.com/images/deploy-to-render-button.svg" alt="Deploy to Koyeb" height="26"></a>
<a href="https://zeabur.com/templates/5FQIGX?referralCode=reycn">
  <img src="https://zeabur.com/button.svg" alt="Deploy on Zeabur" height="26"></a>
<a href="https://app.koyeb.com/deploy?type=git&builder=buildpack&repository=github.com/GBabelDocUI/GBabelDocUI-next&branch=main&name=pdf-math-translate">
  <img src="https://www.koyeb.com/static/images/deploy/button.svg" alt="Deploy to Koyeb" height="26"></a>
</div>

-->

<div align="right"> 
<h6><small>このページの一部のコンテンツは GPT によって翻訳されており、エラーが含まれている可能性があります。</small></h6>