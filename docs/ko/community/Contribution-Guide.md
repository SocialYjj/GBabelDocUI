# Contributing to GBabelDocUI

GBabelDocUI is a multi-user Web UI adaptation layer based on the official `pdf2zh-next` runtime. Contributions that improve authentication, user isolation, task handling, translation settings, PDF output, documentation and deployment are welcome.

## Before opening a pull request

1. Read [NOTICE](https://github.com/SocialYjj/GBabelDocUI/blob/main/NOTICE) and keep the upstream licenses and copyright notices intact.
2. Do not include `data/`, `yuan/`, `.env` files, API keys, databases, uploaded PDFs, generated outputs or local caches.
3. Keep the single-process execution model: do not introduce multiple workers or replicas that share one `data/` directory.
4. For a significant behavior or dependency change, open an issue first and describe the migration or operational impact.

## Development and verification

```bash
uv sync --dev --frozen
uv run pytest -q
uv run ruff check gbabeldocui tests
uv run ruff format --check gbabeldocui tests
node --check gbabeldocui/static/js/api.js
node --check gbabeldocui/static/js/auth.js
node --check gbabeldocui/static/js/i18n.js
docker compose config --quiet
```

Use a feature branch and explain the user-visible behavior, data-preservation impact and verification performed in the pull request. Update the English and Chinese documentation when behavior or deployment instructions change; update other language pages when the corresponding translation is available.

## Documentation translations

Documentation translations are maintained in this repository. Edit the relevant file under `docs/<locale>/` and submit the change as a normal pull request. There is no external Weblate project for GBabelDocUI.

## License

By contributing, you agree that your contribution is distributed under the repository's [AGPL-3.0 License](https://github.com/SocialYjj/GBabelDocUI/blob/main/LICENSE).