[**Começar**](./getting-started.md) > **Uso** > **Linha de comando** _(atual)_

---

> **Nota de escopo:** Esta página é uma referência para a [interface oficial de linha de comando do `pdf2zh-next`](https://github.com/PDFMathTranslate-next/PDFMathTranslate-next). Ela não documenta a Web UI do GBabelDocUI. Para a Web UI do GBabelDocUI, consulte [`USAGE_webui.md`](./USAGE_webui.md) e as instruções do Docker. Não substitua `pdf2zh_next` por `gbabeldocui`: os argumentos de linha de comando não são compatíveis.

### Usar PDFMathTranslate via linha de comando

#### Uso Básico

Após a Instalação, digite este comando para traduzir seu PDF.

```bash
pdf2zh_next document.pdf
```

> [!NOTE]
> 
> Se o caminho do arquivo contiver espaços, por favor, coloque-o entre aspas.
> 
> ```bash
> pdf2zh_next "path with spaces/document.pdf"
> ```

Após executar a tradução, arquivos são gerados no **diretório de trabalho atual**.

> [!TIP]
> **Onde está o meu "Diretório de Trabalho Atual"?**
> Antes de inserir um comando no terminal, você pode ver um nome de caminho exibido no seu terminal:
> 
> ```powershell
> PS C:\Users\XXX>
> ```
> 
> Este diretório é o "*Diretório de trabalho atual*".
> 
> Se não houver um nome de caminho, tente executar este comando no terminal:
> 
> ```bash
> pwd
> ```
> 
> Após executar este comando, um nome de caminho será exibido. Este nome de caminho é o "**Diretório de trabalho atual**". Os arquivos traduzidos aparecerão aqui.

---

#### Opções avançadas

Para explicações detalhadas de parâmetros adicionais da linha de comando, consulte [opções avançadas](./../advanced/advanced.md).

<div align="right"> 
<h6><small>Parte do conteúdo desta página foi traduzida pelo GPT e pode conter erros.</small></h6>