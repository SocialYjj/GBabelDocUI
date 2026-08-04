[**Getting Started**](./getting-started.md) > **Installation** > **Docker** _(current)_

---

### Install GBabelDocUI via docker

#### What is docker?

[Docker](https://docs.docker.com/get-started/docker-overview/) is an open platform for developing, shipping, and running applications. Docker enables you to separate your applications from your infrastructure so you can deliver software quickly. With Docker, you can manage your infrastructure in the same ways you manage your applications. By taking advantage of Docker's methodologies for shipping, testing, and deploying code, you can significantly reduce the delay between writing code and running it in production.

#### Installation

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
<h4>2. Enter this URL in your default browser to open the WebUI page:</h4>

```
http://localhost:7860/
```

> [!NOTE]
> If you encounter any issues during use WebUI, please refer to [Usage --> WebUI](./USAGE_webui.md).

> [!NOTE]
> If you encounter any issues during use command line, please refer to [Usage --> Command Line](./USAGE_commandline.md).
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