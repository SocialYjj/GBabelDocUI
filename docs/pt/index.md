# GBabelDocUI

GBabelDocUI é uma interface Web auto-hospedada e multiusuário para tradução de PDF com BabelDOC.

O projeto deriva de eaiu/GBabelDocUI e inclui um subconjunto verificado do runtime pdf2zh-next 2.9.0. A CLI, a interface Gradio e a API HTTP upstream não estão incluídas.

## Recursos

- Contas, configurações, arquivos, tarefas e histórico isolados por usuário.
- Cookies HttpOnly, proteção CSRF, limitação de login e de sessões.
- Validação do PDF, tamanho, páginas, cota de armazenamento e concorrência.
- Configuração Web para OpenAI, Azure OpenAI e Google Gemini.
- Persistência SQLite e implantação reforçada de instância única com Docker Compose.

## Início rápido

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

Depois, abra `http://127.0.0.1:7860/login.html`.

## Limites de implantação

- Acesso público exige proxy reverso HTTPS e `GBABELDOCUI_COOKIE_SECURE=true`.
- O primeiro administrador é criado localmente; inicialização remota exige um `GBABELDOCUI_SETUP_TOKEN` de uso único.
- Cada diretório de dados aceita apenas um processo e uma réplica.
- `data/` pode conter contas, chaves API, PDFs e resultados e não deve ser publicado.

## Documentação

- [Docker](./getting-started/INSTALLATION_docker.md)
- [uv](./getting-started/INSTALLATION_uv.md)
- [Web UI](./getting-started/USAGE_webui.md)
- [Advanced reference](./advanced/advanced.md)

## Código-fonte e licença

GBabelDocUI e o subconjunto integrado são distribuídos sob AGPL-3.0. NOTICE e UPSTREAM.md registram a origem, os checksums e as alterações.

- [AGPL-3.0](https://github.com/SocialYjj/GBabelDocUI/blob/main/LICENSE)
- [NOTICE](https://github.com/SocialYjj/GBabelDocUI/blob/main/NOTICE)
- [UPSTREAM.md](https://github.com/SocialYjj/GBabelDocUI/blob/main/gbabeldocui/_vendor/pdf2zh_next/UPSTREAM.md)
