<div align="center">

<img src="../images/banner.png" width="320px"  alt="banner"/>

<h2 id="заголовок">GBabelDocUI</h2>

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

- 📊 Сохранение формул, диаграмм, оглавления и аннотаций _([предварительный просмотр](#предварительный-просмотр))_.
- 🌐 Поддержка [множества языков](./supported_languages.md) и разнообразных [служб перевода](./advanced/Documentation-of-Translation-Services.md).
- 🤖 Предоставляет [инструмент командной строки](./getting-started/USAGE_commandline.md), [интерактивный пользовательский интерфейс](./getting-started/USAGE_webui.md) и [Docker](./getting-started/INSTALLATION_docker.md)

<!-- Feel free to provide feedback in [GitHub Issues](https://github.com/SocialYjj/GBabelDocUI/issues) or [Telegram Group](https://t.me/+Z9_SgnxmsmA5NzBl). -->


<h2 id="предпросмотр">Предпросмотр</h2>

<div align="center">
<!-- <img src="../images/preview.gif" width="80%"  alt="preview"/> -->
<img src="https://s.immersivetranslate.com/assets/r2-uploads/images/babeldoc-preview.png" width="80%"/>
</div>

<h2 id="демо">Онлайн-сервис 🌟</h2>

Вы можете опробовать наше приложение, используя любой из следующих сервисов:

- [Immersive Translate - BabelDOC](https://app.immersivetranslate.com/babel-doc/) Доступна бесплатная квота использования; подробности смотрите в разделе FAQ на странице.

<h2 id="установка">Установка и использование</h2>

### Установка

1. [**Windows EXE**](./getting-started/INSTALLATION_winexe.md) <small>Рекомендуется для Windows</small>
2. [**Docker**](./getting-started/INSTALLATION_docker.md) <small>Рекомендуется для Linux</small>
3. [**uv** (менеджер пакетов Python)](./getting-started/INSTALLATION_uv.md) <small>Рекомендуется для macOS</small>

---

### Использование

1. [Использование **WebUI**](./getting-started/USAGE_webui.md)
2. [Использование **Плагина Zotero**](https://github.com/guaguastandup/zotero-pdf2zh) (Сторонняя программа)
3. [Использование **Командной строки**](./getting-started/USAGE_commandline.md)

Для различных случаев использования мы предоставляем различные методы работы с нашей программой. Подробнее смотрите на [этой странице](./getting-started/getting-started.md).

<h2 id="usage">Расширенные параметры</h2>

Подробные объяснения смотрите в нашем документе о [Расширенном использовании](./advanced/advanced.md) для получения полного списка каждой опции.

<h2 id="downstream">Вторичная разработка (API)</h2>

<!-- <!-- For downstream applications, please refer to our document about [API Details](./docs/APIS.md) for futher information about: -->

- [Python API](./advanced/API/python.md), как использовать программу в других программах на Python
<!-- - [HTTP API](./docs/APIS.md#api-http), how to communicate with a server with the program installed -->

<h2 id="кодязыка">Код языка</h2>

Если вы не знаете, какой код использовать для перевода на нужный вам язык, ознакомьтесь с [этой документацией](./advanced/Language-Codes.md)

<h2 id="благодарности">Благодарности</h2>

- [Immersive Translation](https://immersivetranslate.com) спонсирует ежемесячные коды для активации Pro-подписки для активных участников этого проекта, подробности см. в: [CONTRIBUTOR_REWARD.md](https://github.com/funstory-ai/BabelDOC/blob/main/docs/CONTRIBUTOR_REWARD.md)

- [SiliconFlow](https://siliconflow.cn) предоставляет бесплатный сервис перевода для этого проекта, работающий на основе больших языковых моделей (LLM).

- Версия 1.x: [Byaidu/PDFMathTranslate](https://github.com/Byaidu/PDFMathTranslate)


- Бэкенд: [BabelDOC](https://github.com/funstory-ai/BabelDOC)

- Библиотека для работы с PDF: [PyMuPDF](https://github.com/pymupdf/PyMuPDF)

- Парсинг PDF: [Pdfminer.six](https://github.com/pdfminer/pdfminer.six)

- Предпросмотр PDF: [Gradio PDF](https://github.com/freddyaboulton/gradio-pdf)

- Анализ макета: [DocLayout-YOLO](https://github.com/opendatalab/DocLayout-YOLO)

- Стандарты PDF: [PDF Explained](https://zxyle.github.io/PDF-Explained/), [PDF Cheat Sheets](https://pdfa.org/resource/pdf-cheat-sheets/)

- Многоязычные шрифты: см. [BabelDOC-Assets](https://github.com/funstory-ai/BabelDOC-Assets)

- [Asynchronize](https://github.com/multimeric/Asynchronize/tree/master?tab=readme-ov-file)

- [Расширенное логирование с использованием многопроцессорности](https://github.com/SebastianGrans/Rich-multiprocess-logging/tree/main)



<h2 id="conduct">Перед отправкой кода</h2>

Мы приветствуем активное участие участников, чтобы сделать pdf2zh лучше. Прежде чем вы будете готовы отправить свой код, пожалуйста, ознакомьтесь с нашим [Кодексом поведения](./CODE_OF_CONDUCT.md) и [Руководством по внесению вклада](./community/Contribution-Guide.md).

<h2 id="contrib">Участники</h2>

<!-- <a href="https://github.com/SocialYjj/GBabelDocUI/graphs/contributors">
  <img src="https://opencollective.com/PDFMathTranslate/contributors.svg?width=890&button=false" />
</a> -->

<!-- ![Alt](https://repobeats.axiom.co/api/embed/45529651750579e099960950f757449a410477ad.svg "Repobeats analytics image") -->

<h2 id="star_hist">История звезд</h2>

<a href="https://star-history.com/#SocialYjj/GBabelDocUI&Date">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=SocialYjj/GBabelDocUI&type=Date&theme=dark" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=SocialYjj/GBabelDocUI&type=Date" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=SocialYjj/GBabelDocUI&type=Date"/>
 </picture>
</a>

<div align="right"> 
<h6><small>Часть содержимого этой страницы была переведена GPT и может содержать ошибки.</small></h6>
