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

- 📊 Preserva fórmulas, gráficos, tabla de contenidos y anotaciones _([vista previa](#vista-previa))_.
- 🌐 Soporta [múltiples idiomas](./supported_languages.md), y diversos [servicios de traducción](./advanced/Documentation-of-Translation-Services.md).
- 🤖 Proporciona [herramienta de línea de comandos](./getting-started/USAGE_commandline.md), [interfaz de usuario interactiva](./getting-started/USAGE_webui.md), y [Docker](./getting-started/INSTALLATION_docker.md)

<!-- Feel free to provide feedback in [GitHub Issues](https://github.com/SocialYjj/GBabelDocUI/issues) or [Telegram Group](https://t.me/+Z9_SgnxmsmA5NzBl). -->


<h2 id="vista-previa">Vista previa</h2>

<div align="center">
<!-- <img src="../images/preview.gif" width="80%"  alt="preview"/> -->
<img src="https://s.immersivetranslate.com/assets/r2-uploads/images/babeldoc-preview.png" width="80%"/>
</div>

<h2 id="demo">Servicio en línea 🌟</h2>

Puedes probar nuestra aplicación utilizando cualquiera de los siguientes servicios:

- [Immersive Translate - BabelDOC](https://app.immersivetranslate.com/babel-doc/) Hay una cuota de uso gratuita disponible; consulte la sección de Preguntas frecuentes en la página para más detalles.

<h2 id="instalacion">Instalación y Uso</h2>

### Instalación

1. [**Windows EXE**](./getting-started/INSTALLATION_winexe.md) <small>Recomendado para Windows</small>
2. [**Docker**](./getting-started/INSTALLATION_docker.md) <small>Recomendado para Linux</small>
3. [**uv** (un gestor de paquetes de Python)](./getting-started/INSTALLATION_uv.md) <small>Recomendado para macOS</small>

---

### Uso

1. [Usando **WebUI**](./getting-started/USAGE_webui.md)
2. [Usando **Complemento de Zotero**](https://github.com/guaguastandup/zotero-pdf2zh) (Programa de terceros)
3. [Usando **Línea de comandos**](./getting-started/USAGE_commandline.md)

Para diferentes casos de uso, proporcionamos métodos distintos para usar nuestro programa. Consulta [esta página](./getting-started/getting-started.md) para obtener más información.

<h2 id="uso">Opciones avanzadas</h2>

Para explicaciones detalladas, consulta nuestro documento sobre [Uso avanzado](./advanced/advanced.md) para obtener una lista completa de cada opción.

<h2 id="desarrollo-secundario">Desarrollo secundario (APIs)</h2>

<!-- <!-- For downstream applications, please refer to our document about [API Details](./docs/APIS.md) for futher information about: -->

- [Python API](./advanced/API/python.md), cómo usar el programa en otros programas Python
<!-- - [HTTP API](./docs/APIS.md#api-http), how to communicate with a server with the program installed -->

<h2 id="códigoidioma">Language Code</h2>

Si no sabes qué código usar para traducir al idioma que necesitas, consulta [esta documentación](./advanced/Language-Codes.md)

<h2 id="agradecimientos">Acknowledgements</h2>

- [Immersive Translation](https://immersivetranslate.com) patrocina códigos de canje mensuales de membresía Pro para los contribuyentes activos de este proyecto, consulta los detalles en: [CONTRIBUTOR_REWARD.md](https://github.com/funstory-ai/BabelDOC/blob/main/docs/CONTRIBUTOR_REWARD.md)

- [SiliconFlow](https://siliconflow.cn) proporciona un servicio de traducción gratuito para este proyecto, impulsado por modelos de lenguaje grandes (LLMs).

- Versión 1.x: [Byaidu/PDFMathTranslate](https://github.com/Byaidu/PDFMathTranslate)


- backend: [BabelDOC](https://github.com/funstory-ai/BabelDOC)

- Biblioteca PDF: [PyMuPDF](https://github.com/pymupdf/PyMuPDF)

- Análisis de PDF: [Pdfminer.six](https://github.com/pdfminer/pdfminer.six)

- Vista previa de PDF: [Gradio PDF](https://github.com/freddyaboulton/gradio-pdf)

- Análisis de diseño: [DocLayout-YOLO](https://github.com/opendatalab/DocLayout-YOLO)

- Estándares PDF: [PDF Explained](https://zxyle.github.io/PDF-Explained/), [PDF Cheat Sheets](https://pdfa.org/resource/pdf-cheat-sheets/)

- Fuente multilingüe: consulta [BabelDOC-Assets](https://github.com/funstory-ai/BabelDOC-Assets)

- [Asynchronize](https://github.com/multimeric/Asynchronize/tree/master?tab=readme-ov-file)

- [Registro enriquecido con multiprocesamiento](https://github.com/SebastianGrans/Rich-multiprocess-logging/tree/main)



<h2 id="conduct">Antes de enviar tu código</h2>

Damos la bienvenida a la participación activa de los colaboradores para mejorar pdf2zh. Antes de que estés listo para enviar tu código, consulta nuestro [Código de Conducta](./CODE_OF_CONDUCT.md) y [Guía de Contribución](./community/Contribution-Guide.md).

<h2 id="contrib">Colaboradores</h2>

<!-- <a href="https://github.com/SocialYjj/GBabelDocUI/graphs/contributors">
  <img src="https://opencollective.com/PDFMathTranslate/contributors.svg?width=890&button=false" />
</a> -->

<!-- ![Alt](https://repobeats.axiom.co/api/embed/45529651750579e099960950f757449a410477ad.svg "Repobeats analytics image") -->

<h2 id="historial_estrellas">Historial de Estrellas</h2>

<a href="https://star-history.com/#SocialYjj/GBabelDocUI&Date">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=SocialYjj/GBabelDocUI&type=Date&theme=dark" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=SocialYjj/GBabelDocUI&type=Date" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=SocialYjj/GBabelDocUI&type=Date"/>
 </picture>
</a>

<div align="right"> 
<h6><small>Parte del contenido de esta página ha sido traducido por GPT y puede contener errores.</small></h6>
