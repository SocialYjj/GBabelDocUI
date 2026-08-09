# Usar a interface Web do GBabelDocUI

O serviço não abre o navegador automaticamente. Inicie-o e abra manualmente a página de login.

## Requisitos

- Python 3.10–3.13
- Git
- [uv](https://docs.astral.sh/uv/)

## Executar a partir do repositório

```bash
git clone https://github.com/SocialYjj/GBabelDocUI.git
cd GBabelDocUI
uv sync --frozen
```

Para HTTP local, desative o atributo Secure do cookie:

=== "Linux/macOS"

    ```bash
    export GBABELDOCUI_COOKIE_SECURE=false
    uv run gbabeldocui
    ```

=== "Windows PowerShell"

    ```powershell
    $env:GBABELDOCUI_COOKIE_SECURE = "false"
    uv run gbabeldocui
    ```

Depois, abra `http://127.0.0.1:7860/login.html`.

## Primeiro uso

1. Crie o primeiro administrador na página de login local.
2. Configure OpenAI, Azure OpenAI ou Google Gemini em Configurações.
3. Selecione idiomas, saída, intervalo de páginas e opções de PDF.
4. Envie um PDF, inicie a tarefa e baixe o resultado no histórico.

As chaves API salvas permanecem no servidor. Não confirme nem publique o diretório `data/`.

Para contêineres, use o guia Docker Compose. Implantação pública exige HTTPS e uma instância por diretório de dados.
