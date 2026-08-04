<div align="center">

<img src="../images/banner.png" width="320px"  alt="banner"/>

<h2 id="título">GBabelDocUI</h2>

<p>
  <a href="https://github.com/SocialYjj/GBabelDocUI/pkgs/container/gbabeldocui">
    <img src="https://img.shields.io/badge/GHCR-GBabelDocUI-blue"></a>
  <!-- <a href="https://huggingface.co/spaces/reycn/PDFMathTranslate-Docker">
    <img src="https://img.shields.io/badge/%F0%9F%A4%97-Online%20Demo-FF9E0D"></a> -->
  <!-- <a href="https://www.modelscope.cn/studios/AI-ModelScope/PDFMathTranslate"> -->
    <!-- <img src="https://img.shields.io/badge/ModelScope-Demo-blue"></a> -->
  <!-- <a href="https://github.com/SocialYjj/GBabelDocUI/pulls">
    <img src="https://img.shields.io/badge/contributions-welcome-green"></a> -->
  <a href="https://t.me/+Z9_SgnxmsmA5NzBl">
    <img src="https://img.shields.io/badge/Telegram-2CA5E0?style=flat-squeare&logo=telegram&logoColor=white"></a>
  <!-- License -->
  <a href="https://github.com/SocialYjj/GBabelDocUI/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/SocialYjj/GBabelDocUI"></a>
</p>

<a href="https://trendshift.io/repositories/12424" target="_blank"><img src="https://trendshift.io/api/badge/repositories/12424" alt="Byaidu%2FPDFMathTranslate | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>

</div>

GBabelDocUI is a multi-user Web UI adaptation layer based on the official pdf2zh-next runtime and BabelDOC.

- 📊 Preserve fórmulas, gráficos, sumário e anotações _([prévia](#prévia))_.
- 🌐 Suporta [múltiplos idiomas](./supported_languages.md) e diversos [serviços de tradução](./advanced/Documentation-of-Translation-Services.md).
- 🤖 Oferece [ferramenta de linha de comando](./getting-started/USAGE_commandline.md), [interface de usuário interativa](./getting-started/USAGE_webui.md) e [Docker](./getting-started/INSTALLATION_docker.md)

<!-- Feel free to provide feedback in [GitHub Issues](https://github.com/SocialYjj/GBabelDocUI/issues) or [Telegram Group](https://t.me/+Z9_SgnxmsmA5NzBl). -->


<h2 id="preview">Pré-visualização</h2>

<div align="center">
<!-- <img src="../images/preview.gif" width="80%"  alt="preview"/> -->
<img src="https://s.immersivetranslate.com/assets/r2-uploads/images/babeldoc-preview.png" width="80%"/>
</div>

<h2 id="demo">Serviço Online 🌟</h2>

Você pode experimentar nossa aplicação usando qualquer um dos seguintes serviços:

- [Immersive Translate - BabelDOC](https://app.immersivetranslate.com/babel-doc/) Cota de uso gratuito disponível; consulte a seção de Perguntas frequentes na página para obter detalhes.

<h2 id="instalacao">Instalação e Uso</h2>

### Instalação

1. [**Windows EXE**](./getting-started/INSTALLATION_winexe.md) <small>Recomendado para Windows</small>
2. [**Docker**](./getting-started/INSTALLATION_docker.md) <small>Recomendado para Linux</small>
3. [**uv** (um gerenciador de pacotes Python)](./getting-started/INSTALLATION_uv.md) <small>Recomendado para macOS</small>

---

### Uso

1. [Usando **WebUI**](./getting-started/USAGE_webui.md)
2. [Usando **Plugin do Zotero**](https://github.com/guaguastandup/zotero-pdf2zh) (Programa de terceiros)
3. [Usando **Linha de comando**](./getting-started/USAGE_commandline.md)

Para diferentes casos de uso, fornecemos métodos distintos para usar nosso programa. Confira [esta página](./getting-started/getting-started.md) para mais informações.

<h2 id="uso">Opções Avançadas</h2>

Para explicações detalhadas, consulte nosso documento sobre [Uso Avançado](./advanced/advanced.md) para obter uma lista completa de cada opção.

<h2 id="desenvolvimento-secundario">Desenvolvimento Secundário (APIs)</h2>

<!-- <!-- For downstream applications, please refer to our document about [API Details](./docs/APIS.md) for futher information about: -->

- [API Python](./advanced/API/python.md), como usar o programa em outros programas Python
<!-- - [HTTP API](./docs/APIS.md#api-http), how to communicate with a server with the program installed -->

<h2 id="código-do-idioma">Código do Idioma</h2>

Se você não sabe qual código usar para traduzir para o idioma que precisa, consulte [esta documentação](./advanced/Language-Codes.md)

<h2 id="agradecimentos">Agradecimentos</h2>

- [Immersive Translation](https://immersivetranslate.com) patrocina códigos de resgate de assinatura Pro mensal para colaboradores ativos deste projeto, veja os detalhes em: [CONTRIBUTOR_REWARD.md](https://github.com/funstory-ai/BabelDOC/blob/main/docs/CONTRIBUTOR_REWARD.md)

- [SiliconFlow](https://siliconflow.cn) fornece um serviço de tradução gratuito para este projeto, alimentado por grandes modelos de linguagem (LLMs).

- Versão 1.x: [Byaidu/PDFMathTranslate](https://github.com/Byaidu/PDFMathTranslate)


- backend: [BabelDOC](https://github.com/funstory-ai/BabelDOC)

- Biblioteca PDF: [PyMuPDF](https://github.com/pymupdf/PyMuPDF)

- Análise de PDF: [Pdfminer.six](https://github.com/pdfminer/pdfminer.six)

- Visualização de PDF: [Gradio PDF](https://github.com/freddyaboulton/gradio-pdf)

- Análise de Layout: [DocLayout-YOLO](https://github.com/opendatalab/DocLayout-YOLO)

- Padrões PDF: [PDF Explained](https://zxyle.github.io/PDF-Explained/), [PDF Cheat Sheets](https://pdfa.org/resource/pdf-cheat-sheets/)

- Fonte Multilíngue: veja [BabelDOC-Assets](https://github.com/funstory-ai/BabelDOC-Assets)

- [Asynchronize](https://github.com/multimeric/Asynchronize/tree/master?tab=readme-ov-file)

- [Registro rico com multiprocessamento](https://github.com/SebastianGrans/Rich-multiprocess-logging/tree/main)



<h2 id="conduta">Antes de enviar seu código</h2>

Agradecemos a participação ativa dos colaboradores para tornar o pdf2zh melhor. Antes de estar pronto para enviar seu código, consulte nosso [Código de Conduta](./CODE_OF_CONDUCT.md) e [Guia de Contribuição](./community/Contribution-Guide.md).

<h2 id="contribuidores">Colaboradores</h2>

<!-- <a href="https://github.com/SocialYjj/GBabelDocUI/graphs/contributors">
  <img src="https://opencollective.com/PDFMathTranslate/contributors.svg?width=890&button=false" />
</a> -->

<!-- ![Alt](https://repobeats.axiom.co/api/embed/45529651750579e099960950f757449a410477ad.svg "Repobeats analytics image") -->

<h2 id="histórico_de_estrelas">Star History</h2>

<a href="https://star-history.com/#SocialYjj/GBabelDocUI&Date">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=SocialYjj/GBabelDocUI&type=Date&theme=dark" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=SocialYjj/GBabelDocUI&type=Date" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=SocialYjj/GBabelDocUI&type=Date"/>
 </picture>
</a>

<div align="right"> 
<h6><small>Parte do conteúdo desta página foi traduzida pelo GPT e pode conter erros.</small></h6>
