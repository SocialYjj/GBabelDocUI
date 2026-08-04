[**Начало работы**](./getting-started.md) > **Установка** > **Docker** _(текущая)_

---

### Установка GBabelDocUI через docker

#### Что такое Docker?

[Docker](https://docs.docker.com/get-started/docker-overview/) — это открытая платформа для разработки, доставки и запуска приложений. Docker позволяет отделить ваши приложения от инфраструктуры, чтобы вы могли быстро доставлять программное обеспечение. С Docker вы можете управлять своей инфраструктурой так же, как и приложениями. Используя преимущества методологий Docker для доставки, тестирования и развертывания кода, вы можете значительно сократить задержку между написанием кода и его запуском в производственной среде.

#### Установка

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
<h4>2. Введите этот URL в вашем браузере по умолчанию, чтобы открыть страницу WebUI:</h4>

```
http://localhost:7860/
```

> [!NOTE]
> Если у вас возникли проблемы при использовании WebUI, обратитесь к разделу [Использование --> WebUI](./USAGE_webui.md).

> [!NOTE]
> Если у вас возникли проблемы при использовании командной строки, обратитесь к разделу [Использование --> Командная строка](./USAGE_commandline.md).
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
<h6><small>Часть содержимого этой страницы была переведена GPT и может содержать ошибки.</small></h6>