[**Erste Schritte**](./getting-started.md) > **Installation** > **Docker** _(aktuell)_

---

### Installieren Sie GBabelDocUI über Docker

#### Was ist Docker?

[Docker](https://docs.docker.com/get-started/docker-overview/) ist eine offene Plattform für die Entwicklung, den Versand und die Ausführung von Anwendungen. Docker ermöglicht es Ihnen, Ihre Anwendungen von Ihrer Infrastruktur zu trennen, sodass Sie Software schnell bereitstellen können. Mit Docker können Sie Ihre Infrastruktur auf die gleiche Weise verwalten wie Ihre Anwendungen. Durch die Nutzung der Methoden von Docker für den Versand, die Tests und die Bereitstellung von Code können Sie die Verzögerung zwischen dem Schreiben von Code und dessen Ausführung in der Produktion erheblich reduzieren.

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
<h4>2. Geben Sie diese URL in Ihrem Standardbrowser ein, um die WebUI-Seite zu öffnen:</h4>

```
http://localhost:7860/
```

> [!NOTE]
> Wenn Sie Probleme bei der Verwendung von WebUI haben, lesen Sie bitte [Verwendung --> WebUI](./USAGE_webui.md).

> [!NOTE]
> Wenn Sie Probleme bei der Verwendung der Kommandozeile haben, lesen Sie bitte [Verwendung --> Kommandozeile](./USAGE_commandline.md).
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
<h6><small>Ein Teil des Inhalts dieser Seite wurde von GPT übersetzt und kann Fehler enthalten.</small></h6>