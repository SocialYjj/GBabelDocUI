# GBabelDocUI

GBabelDocUI es una interfaz web autoalojada y multiusuario para traducir PDF con BabelDOC.

El proyecto deriva de eaiu/GBabelDocUI e incluye un subconjunto verificado del entorno de ejecución de pdf2zh-next 2.9.0. No incluye la CLI, la interfaz Gradio ni la API HTTP del proyecto original.

## Funciones

- Cuentas, ajustes, archivos, tareas e historial aislados por usuario.
- Cookies HttpOnly, protección CSRF, límites de inicio de sesión y de sesiones.
- Validación del PDF, tamaño, páginas, cuota de almacenamiento y concurrencia.
- Configuración web para OpenAI, Azure OpenAI y Google Gemini.
- Persistencia SQLite y despliegue endurecido de una sola instancia con Docker Compose.

## Inicio rápido

### Docker Compose

```bash
git clone https://github.com/SocialYjj/GBabelDocUI.git
cd GBabelDocUI
mkdir -p data
sudo chown -R 10001:10001 data  # Linux bind mounts only
docker compose up -d --build
```

### uv

```bash
git clone https://github.com/SocialYjj/GBabelDocUI.git
cd GBabelDocUI
uv sync --frozen
export GBABELDOCUI_COOKIE_SECURE=false
uv run gbabeldocui
```

Después, abra `http://127.0.0.1:7860/login.html`.

## Límites de despliegue

- El acceso público requiere un proxy inverso HTTPS y `GBABELDOCUI_COOKIE_SECURE=true`.
- El primer administrador se crea localmente; la inicialización remota requiere un `GBABELDOCUI_SETUP_TOKEN` de un solo uso.
- Cada directorio de datos admite un solo proceso y una sola réplica.
- `data/` puede contener cuentas, claves API, PDF y resultados; no debe publicarse.

## Documentación

- [Docker](./getting-started/INSTALLATION_docker.md)
- [uv](./getting-started/INSTALLATION_uv.md)
- [Web UI](./getting-started/USAGE_webui.md)
- [Advanced reference](./advanced/advanced.md)

## Código fuente y licencia

GBabelDocUI y el subconjunto integrado se distribuyen bajo AGPL-3.0. NOTICE y UPSTREAM.md documentan la procedencia, las sumas de comprobación y los cambios.

- [AGPL-3.0](https://github.com/SocialYjj/GBabelDocUI/blob/main/LICENSE)
- [NOTICE](https://github.com/SocialYjj/GBabelDocUI/blob/main/NOTICE)
- [UPSTREAM.md](https://github.com/SocialYjj/GBabelDocUI/blob/main/gbabeldocui/_vendor/pdf2zh_next/UPSTREAM.md)
