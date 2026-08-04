# Improving Documentation Translations

GBabelDocUI does not use an external Weblate project. Documentation translations are reviewed through normal pull requests in [SocialYjj/GBabelDocUI](https://github.com/SocialYjj/GBabelDocUI).

## How to contribute

1. Choose the relevant file under `docs/<locale>/`.
2. Keep commands, environment variable names, API paths and file paths identical to the canonical documentation.
3. Do not add real accounts, API keys, tokens, PDFs, generated outputs or VPS data to documentation examples.
4. Run `git diff --check` and, when possible, `uv run mkdocs build` before opening a pull request.
5. Describe the language and pages changed in the pull request.

If a translation conflicts with the current Web UI behavior, update the documentation to match the repository implementation and mention the discrepancy in the pull request. English and Chinese are the reference pages for deployment and behavior; other language pages should not reintroduce instructions for the upstream project.