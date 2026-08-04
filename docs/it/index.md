<div align="center">

<img src="../images/banner.png" width="320px"  alt="banner"/>

<h2 id="titolo">GBabelDocUI</h2>

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

- 📊 Conserva formule, grafici, indice e annotazioni _([anteprima](#anteprima))_.
- 🌐 Supporta [molte lingue](./supported_languages.md) e diversi [servizi di traduzione](./advanced/Documentation-of-Translation-Services.md).
- 🤖 Fornisce [strumento da riga di comando](./getting-started/USAGE_commandline.md), [interfaccia utente interattiva](./getting-started/USAGE_webui.md) e [Docker](./getting-started/INSTALLATION_docker.md)

<!-- Feel free to provide feedback in [GitHub Issues](https://github.com/SocialYjj/GBabelDocUI/issues) or [Telegram Group](https://t.me/+Z9_SgnxmsmA5NzBl). -->


<h2 id="anteprima">Anteprima</h2>

<div align="center">
<!-- <img src="../images/preview.gif" width="80%"  alt="preview"/> -->
<img src="https://s.immersivetranslate.com/assets/r2-uploads/images/babeldoc-preview.png" width="80%"/>
</div>

<h2 id="demo">Online Service 🌟</h2>

Puoi provare la nostra applicazione utilizzando uno dei seguenti servizi:

- [Immersive Translate - BabelDOC](https://app.immersivetranslate.com/babel-doc/) È disponibile una quota di utilizzo gratuita; per i dettagli, consultare la sezione Domande frequenti nella pagina.

<h2 id="installazione">Installazione e Utilizzo</h2>

### Installazione

1. [**Windows EXE**](./getting-started/INSTALLATION_winexe.md) <small>Consigliato per Windows</small>
2. [**Docker**](./getting-started/INSTALLATION_docker.md) <small>Consigliato per Linux</small>
3. [**uv** (un gestore di pacchetti Python)](./getting-started/INSTALLATION_uv.md) <small>Consigliato per macOS</small>

---

### Utilizzo

1. [Utilizzo di **WebUI**](./getting-started/USAGE_webui.md)
2. [Utilizzo di **Zotero Plugin**](https://github.com/guaguastandup/zotero-pdf2zh) (Programma di terze parti)
3. [Utilizzo di **Riga di comando**](./getting-started/USAGE_commandline.md)

Per diversi casi d'uso, forniamo metodi distinti per utilizzare il nostro programma. Consulta [questa pagina](./getting-started/getting-started.md) per maggiori informazioni.

<h2 id="usage">Opzioni avanzate</h2>

Per spiegazioni dettagliate, si prega di fare riferimento al nostro documento su [Utilizzo avanzato](./advanced/advanced.md) per un elenco completo di ogni opzione.

<h2 id="downstream">Sviluppo secondario (API)</h2>

<!-- <!-- For downstream applications, please refer to our document about [API Details](./docs/APIS.md) for futher information about: -->

- [API Python](./advanced/API/python.md), come utilizzare il programma in altri programmi Python
<!-- - [HTTP API](./docs/APIS.md#api-http), how to communicate with a server with the program installed -->

<h2 id="codice-lingua">Codice lingua</h2>

Se non sai quale codice utilizzare per tradurre nella lingua di cui hai bisogno, consulta [questa documentazione](./advanced/Language-Codes.md)

<h2 id="ringraziamenti">Ringraziamenti</h2>

- [Immersive Translation](https://immersivetranslate.com) sponsorizza codici di riscatto mensili per l'abbonamento Pro per i contributori attivi a questo progetto, vedi i dettagli su: [CONTRIBUTOR_REWARD.md](https://github.com/funstory-ai/BabelDOC/blob/main/docs/CONTRIBUTOR_REWARD.md)

- [SiliconFlow](https://siliconflow.cn) fornisce un servizio di traduzione gratuito per questo progetto, alimentato da grandi modelli linguistici (LLM).

- Versione 1.x: [Byaidu/PDFMathTranslate](https://github.com/Byaidu/PDFMathTranslate)


- backend: [BabelDOC](https://github.com/funstory-ai/BabelDOC)

- Libreria PDF: [PyMuPDF](https://github.com/pymupdf/PyMuPDF)

- Analisi PDF: [Pdfminer.six](https://github.com/pdfminer/pdfminer.six)

- Anteprima PDF: [Gradio PDF](https://github.com/freddyaboulton/gradio-pdf)

- Analisi layout: [DocLayout-YOLO](https://github.com/opendatalab/DocLayout-YOLO)

- Standard PDF: [PDF Explained](https://zxyle.github.io/PDF-Explained/), [PDF Cheat Sheets](https://pdfa.org/resource/pdf-cheat-sheets/)

- Carattere multilingue: vedi [BabelDOC-Assets](https://github.com/funstory-ai/BabelDOC-Assets)

- [Asynchronize](https://github.com/multimeric/Asynchronize/tree/master?tab=readme-ov-file)

- [Registrazione avanzata con multiprocessing](https://github.com/SebastianGrans/Rich-multiprocess-logging/tree/main)



<h2 id="condotta">Prima di inviare il tuo codice</h2>

Accogliamo con favore la partecipazione attiva dei contributori per rendere pdf2zh migliore. Prima di essere pronto a inviare il tuo codice, consulta il nostro [Codice di Condotta](./CODE_OF_CONDUCT.md) e la [Guida al Contributo](./community/Contribution-Guide.md).

<h2 id="contributori">Contributori</h2>

<!-- <a href="https://github.com/SocialYjj/GBabelDocUI/graphs/contributors">
  <img src="https://opencollective.com/PDFMathTranslate/contributors.svg?width=890&button=false" />
</a> -->

<!-- ![Alt](https://repobeats.axiom.co/api/embed/45529651750579e099960950f757449a410477ad.svg "Repobeats analytics image") -->

<h2 id="cronologia_stelle">Cronologia Stelle</h2>

<a href="https://star-history.com/#SocialYjj/GBabelDocUI&Date">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=SocialYjj/GBabelDocUI&type=Date&theme=dark" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=SocialYjj/GBabelDocUI&type=Date" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=SocialYjj/GBabelDocUI&type=Date"/>
 </picture>
</a>

<div align="right"> 
<h6><small>Parte del contenuto di questa pagina è stata tradotta da GPT e potrebbe contenere errori.</small></h6>
