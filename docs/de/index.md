<div align="center">

<img src="../images/banner.png" width="320px"  alt="banner"/>

<h2 id="titel">GBabelDocUI</h2>

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

- 📊 Erhalten Sie Formeln, Diagramme, Inhaltsverzeichnisse und Anmerkungen _([Vorschau](#vorschau))_.
- 🌐 Unterstützt [mehrere Sprachen](./supported_languages.md) und verschiedene [Übersetzungsdienste](./advanced/Documentation-of-Translation-Services.md).
- 🤖 Bietet [Kommandozeilen-Tool](./getting-started/USAGE_commandline.md), [interaktive Benutzeroberfläche](./getting-started/USAGE_webui.md) und [Docker](./getting-started/INSTALLATION_docker.md)

<!-- Feel free to provide feedback in [GitHub Issues](https://github.com/SocialYjj/GBabelDocUI/issues) or [Telegram Group](https://t.me/+Z9_SgnxmsmA5NzBl). -->


<h2 id="vorschau">Vorschau</h2>

<div align="center">
<!-- <img src="../images/preview.gif" width="80%"  alt="preview"/> -->
<img src="https://s.immersivetranslate.com/assets/r2-uploads/images/babeldoc-preview.png" width="80%"/>
</div>

<h2 id="demo">Online Service 🌟</h2>

Sie können unsere Anwendung über einen der folgenden Dienste ausprobieren:

- [Immersive Translate - BabelDOC](https://app.immersivetranslate.com/babel-doc/) Ein kostenloses Nutzungskontingent ist verfügbar; Einzelheiten finden Sie im FAQ-Bereich auf der Seite.

<h2 id="install">Installation und Verwendung</h2>

### Installation

1. [**Windows EXE**](./getting-started/INSTALLATION_winexe.md) <small>Empfohlen für Windows</small>
2. [**Docker**](./getting-started/INSTALLATION_docker.md) <small>Empfohlen für Linux</small>
3. [**uv** (ein Python-Paketmanager)](./getting-started/INSTALLATION_uv.md) <small>Empfohlen für macOS</small>

---

### Verwendung

1. [Verwendung von **WebUI**](./getting-started/USAGE_webui.md)
2. [Verwendung des **Zotero-Plugins**](https://github.com/guaguastandup/zotero-pdf2zh) (Drittanbieter-Programm)
3. [Verwendung der **Kommandozeile**](./getting-started/USAGE_commandline.md)

Für verschiedene Anwendungsfälle bieten wir unterschiedliche Methoden zur Nutzung unseres Programms. Weitere Informationen finden Sie auf [dieser Seite](./getting-started/getting-started.md).

<h2 id="usage">Erweiterte Optionen</h2>

Detaillierte Erklärungen finden Sie in unserem Dokument zur [Erweiterten Verwendung](./advanced/advanced.md) für eine vollständige Liste aller Optionen.

<h2 id="downstream">Weiterentwicklung (APIs)</h2>

<!-- <!-- For downstream applications, please refer to our document about [API Details](./docs/APIS.md) for futher information about: -->

- [Python API](./advanced/API/python.md), wie man das Programm in anderen Python-Programmen verwendet
<!-- - [HTTP API](./docs/APIS.md#api-http), how to communicate with a server with the program installed -->

<h2 id="langcode">Sprachcode</h2>

Wenn Sie nicht wissen, welchen Code Sie verwenden müssen, um in die gewünschte Sprache zu übersetzen, lesen Sie [diese Dokumentation](./advanced/Language-Codes.md)

<h2 id="acknowledgement">Danksagungen</h2>

- [Immersive Translation](https://immersivetranslate.com) sponsert monatliche Pro-Mitgliedschafts-Einlösecodes für aktive Mitwirkende an diesem Projekt. Einzelheiten finden Sie unter: [CONTRIBUTOR_REWARD.md](https://github.com/funstory-ai/BabelDOC/blob/main/docs/CONTRIBUTOR_REWARD.md)

- [SiliconFlow](https://siliconflow.cn) stellt für dieses Projekt einen kostenlosen Übersetzungsdienst bereit, der von großen Sprachmodellen (LLMs) unterstützt wird.

- 1.x Version: [Byaidu/PDFMathTranslate](https://github.com/Byaidu/PDFMathTranslate)


- Backend: [BabelDOC](https://github.com/funstory-ai/BabelDOC)

- PDF-Bibliothek: [PyMuPDF](https://github.com/pymupdf/PyMuPDF)

- PDF-Parsing: [Pdfminer.six](https://github.com/pdfminer/pdfminer.six)

- PDF-Vorschau: [Gradio PDF](https://github.com/freddyaboulton/gradio-pdf)

- Layout-Parsing: [DocLayout-YOLO](https://github.com/opendatalab/DocLayout-YOLO)

- PDF-Standards: [PDF Explained](https://zxyle.github.io/PDF-Explained/), [PDF Cheat Sheets](https://pdfa.org/resource/pdf-cheat-sheets/)

- Mehrsprachige Schriftart: siehe [BabelDOC-Assets](https://github.com/funstory-ai/BabelDOC-Assets)

- [Asynchronize](https://github.com/multimeric/Asynchronize/tree/master?tab=readme-ov-file)

- [Rich logging with multiprocessing](https://github.com/SebastianGrans/Rich-multiprocess-logging/tree/main)



<h2 id="verhalten">Bevor Sie Ihren Code einreichen</h2>

Wir begrüßen die aktive Teilnahme von Mitwirkenden, um pdf2zh besser zu machen. Bevor Sie bereit sind, Ihren Code einzureichen, lesen Sie bitte unseren [Verhaltenskodex](./CODE_OF_CONDUCT.md) und unseren [Leitfaden für Beiträge](./community/Contribution-Guide.md).

<h2 id="mitwirkende">Mitwirkende</h2>

<!-- <a href="https://github.com/SocialYjj/GBabelDocUI/graphs/contributors">
  <img src="https://opencollective.com/PDFMathTranslate/contributors.svg?width=890&button=false" />
</a> -->

<!-- ![Alt](https://repobeats.axiom.co/api/embed/45529651750579e099960950f757449a410477ad.svg "Repobeats analytics image") -->

<h2 id="star_hist">Star History</h2>

<a href="https://star-history.com/#SocialYjj/GBabelDocUI&Date">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=SocialYjj/GBabelDocUI&type=Date&theme=dark" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=SocialYjj/GBabelDocUI&type=Date" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=SocialYjj/GBabelDocUI&type=Date"/>
 </picture>
</a>

<div align="right"> 
<h6><small>Ein Teil des Inhalts dieser Seite wurde von GPT übersetzt und kann Fehler enthalten.</small></h6>
