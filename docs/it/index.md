# GBabelDocUI

GBabelDocUI è un'interfaccia Web multiutente e self-hosted per tradurre PDF con BabelDOC.

Il progetto deriva da eaiu/GBabelDocUI e include un sottoinsieme verificato del runtime pdf2zh-next 2.9.0. Non include la CLI, l'interfaccia Gradio o l'API HTTP upstream.

## Funzionalità

- Account, impostazioni, file, attività e cronologia isolati per utente.
- Cookie HttpOnly, protezione CSRF, limiti di accesso e di sessione.
- Convalida di PDF, dimensione, pagine, quota e concorrenza.
- Configurazione Web per OpenAI, Azure OpenAI e Google Gemini.
- Persistenza SQLite e distribuzione Docker Compose rafforzata a istanza singola.

## Avvio rapido

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

Aprire quindi `http://127.0.0.1:7860/login.html`.

## Limiti di distribuzione

- L'accesso pubblico richiede un reverse proxy HTTPS e `GBABELDOCUI_COOKIE_SECURE=true`.
- Il primo amministratore viene creato localmente; l'inizializzazione remota richiede un `GBABELDOCUI_SETUP_TOKEN` monouso.
- Per ogni directory dati è consentito un solo processo e una sola replica.
- `data/` può contenere account, chiavi API, PDF e risultati e non deve essere pubblicata.

## Documentazione

- [Docker](./getting-started/INSTALLATION_docker.md)
- [uv](./getting-started/INSTALLATION_uv.md)
- [Web UI](./getting-started/USAGE_webui.md)
- [Advanced reference](./advanced/advanced.md)

## Sorgente e licenza

GBabelDocUI e il sottoinsieme integrato sono distribuiti con licenza AGPL-3.0. NOTICE e UPSTREAM.md documentano provenienza, checksum e modifiche.

- [AGPL-3.0](https://github.com/SocialYjj/GBabelDocUI/blob/main/LICENSE)
- [NOTICE](https://github.com/SocialYjj/GBabelDocUI/blob/main/NOTICE)
- [UPSTREAM.md](https://github.com/SocialYjj/GBabelDocUI/blob/main/gbabeldocui/_vendor/pdf2zh_next/UPSTREAM.md)
