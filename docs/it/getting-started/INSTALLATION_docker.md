[**Iniziare**](./getting-started.md) > **Installazione** > **Docker** _(current)_

---

### Installa GBabelDocUI tramite docker

#### Cos'è Docker?

[Docker](https://docs.docker.com/get-started/docker-overview/) è una piattaforma open per lo sviluppo, la spedizione e l'esecuzione di applicazioni. Docker ti consente di separare le tue applicazioni dalla tua infrastruttura in modo da poter fornire software rapidamente. Con Docker, puoi gestire la tua infrastruttura nello stesso modo in cui gestisci le tue applicazioni. Sfruttando le metodologie di Docker per la spedizione, il test e la distribuzione del codice, puoi ridurre significativamente il ritardo tra la scrittura del codice e la sua esecuzione in produzione.

#### Installazione

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
<h4>2. Inserisci questo URL nel tuo browser predefinito per aprire la pagina WebUI:</h4>

```
http://localhost:7860/
```

> [!NOTE]
> Se riscontri problemi durante l'utilizzo di WebUI, consulta [Utilizzo --> WebUI](./USAGE_webui.md).

> [!NOTE]
> Se riscontri problemi durante l'utilizzo della riga di comando, consulta [Utilizzo --> Riga di comando](./USAGE_commandline.md).
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
<h6><small>Parte del contenuto di questa pagina è stata tradotta da GPT e potrebbe contenere errori.</small></h6>