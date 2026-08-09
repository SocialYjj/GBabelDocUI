# GBabelDocUI

GBabelDocUI est une interface Web auto-hébergée et multi-utilisateur pour traduire des PDF avec BabelDOC.

Le projet est dérivé de eaiu/GBabelDocUI et intègre un sous-ensemble vérifié de pdf2zh-next 2.9.0. Il n'inclut ni la CLI, ni l'interface Gradio, ni l'API HTTP amont.

## Fonctionnalités

- Comptes, paramètres, fichiers, tâches et historique isolés par utilisateur.
- Cookies HttpOnly, protection CSRF, limitation des connexions et des sessions.
- Validation du PDF, de la taille, des pages, du quota et de la concurrence.
- Configuration Web pour OpenAI, Azure OpenAI et Google Gemini.
- Persistance SQLite et déploiement Docker Compose renforcé en instance unique.

## Démarrage rapide

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

Ouvrez ensuite `http://127.0.0.1:7860/login.html`.

## Limites de déploiement

- L'accès public exige un proxy inverse HTTPS et `GBABELDOCUI_COOKIE_SECURE=true`.
- Le premier administrateur est créé localement ; l'initialisation distante exige un `GBABELDOCUI_SETUP_TOKEN` à usage unique.
- Un seul processus et une seule réplique sont autorisés par répertoire de données.
- `data/` peut contenir des comptes, clés API, PDF et résultats et ne doit jamais être publié.

## Documentation

- [Docker](./getting-started/INSTALLATION_docker.md)
- [uv](./getting-started/INSTALLATION_uv.md)
- [Web UI](./getting-started/USAGE_webui.md)
- [Advanced reference](./advanced/advanced.md)

## Source et licence

GBabelDocUI et le sous-ensemble intégré sont distribués sous AGPL-3.0. NOTICE et UPSTREAM.md décrivent la provenance, les sommes de contrôle et les modifications.

- [AGPL-3.0](https://github.com/SocialYjj/GBabelDocUI/blob/main/LICENSE)
- [NOTICE](https://github.com/SocialYjj/GBabelDocUI/blob/main/NOTICE)
- [UPSTREAM.md](https://github.com/SocialYjj/GBabelDocUI/blob/main/gbabeldocui/_vendor/pdf2zh_next/UPSTREAM.md)
