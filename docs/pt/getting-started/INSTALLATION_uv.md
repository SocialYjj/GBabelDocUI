[**Começar**](./getting-started.md) > **Instalação** > **uv** _(atual)_

---

> **Nota de escopo:** Esta página é uma referência para a [instalação oficial do `pdf2zh-next` com uv](https://github.com/PDFMathTranslate-next/PDFMathTranslate-next). Ela não documenta a Web UI do GBabelDocUI. Para a Web UI do GBabelDocUI, consulte [`USAGE_webui.md`](./USAGE_webui.md) e as instruções do Docker. Não substitua `pdf2zh_next` por `gbabeldocui`: os argumentos de linha de comando não são compatíveis.

### Instalar PDFMathTranslate via uv

#### O que é uv? Como instalá-lo?

uv é um gerenciador de pacotes e projetos Python extremamente rápido, escrito em Rust.
<br>
Para instalar o uv no seu computador, consulte [este artigo](https://docs.astral.sh/uv/getting-started/installation/).

---

#### Instalação

1. Python instalado (versão >= 3.10 e <= 3.12);

2. Use o seguinte comando para utilizar nosso pacote:

    ```bash
    pip install uv
    uv tool install --python 3.12 pdf2zh-next
    ```

Após a instalação, você pode começar a tradução via **linha de comando** ou **WebUI**.

!!! Warning

    Se você vir o erro `command not found: pdf2zh_next` ao executar, configure as variáveis de ambiente da seguinte forma e tente novamente:

    === "macOS e Linux"

        Adicione o seguinte ao seu ~/.zshrc:

        ```console
        export PATH="$PATH:/Users/Username/.local/bin"
        ```

        Em seguida, reinicie seu terminal

    === "Windows"

        Digite o seguinte no PowerShell:

        ```powershell
        $env:Path = "C:\Users\Username\.local\bin;$env:Path"
        ```

        Em seguida, reinicie seu terminal

> [!NOTE]
> Se você encontrar qualquer problema ao usar o WebUI, consulte [Uso --> WebUI](./USAGE_webui.md).

> [!NOTE]
> Se você encontrar qualquer problema ao usar a linha de comando, consulte [Uso --> Linha de comando](./USAGE_commandline.md).

<div align="right"> 
<h6><small>Parte do conteúdo desta página foi traduzida pelo GPT e pode conter erros.</small></h6>