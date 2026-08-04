[**Commencer**](./getting-started.md) > **Utilisation** > **Ligne de commande** _(current)_

---

> **Périmètre :** Cette page est une référence pour l'[interface de ligne de commande officielle de `pdf2zh-next`](https://github.com/PDFMathTranslate-next/PDFMathTranslate-next). Elle ne documente pas l'interface Web de GBabelDocUI. Pour l'interface Web de GBabelDocUI, consultez [`USAGE_webui.md`](./USAGE_webui.md) et les instructions Docker. Ne remplacez pas `pdf2zh_next` par `gbabeldocui` : leurs arguments de ligne de commande ne sont pas compatibles.

### Utiliser PDFMathTranslate via la ligne de commande

#### Utilisation de base

Après l'installation, veuillez entrer cette commande pour traduire votre PDF.

```bash
pdf2zh_next document.pdf
```

> [!NOTE]
> 
> Si votre chemin d'accès contient des espaces, veuillez l'encadrer de guillemets.
> 
> ```bash
> pdf2zh_next "path with spaces/document.pdf"
> ```

Après avoir exécuté la traduction, les fichiers sont générés dans le **répertoire de travail actuel**.

> [!TIP]
> **Où se trouve mon "Répertoire de travail actuel" ?**
> Avant d'entrer une commande dans le terminal, vous pourriez voir un chemin affiché dans votre terminal :
> 
> ```powershell
> PS C:\Users\XXX>
> ```
> 
> Ce répertoire est le "*Répertoire de travail actuel*".
> 
> S'il n'y a pas de chemin, essayez d'exécuter cette commande dans le terminal :
> 
> ```bash
> pwd
> ```
> 
> Après avoir exécuté cette commande, un chemin sera affiché. Ce chemin est le "**Répertoire de travail actuel**". Les fichiers traduits apparaîtront ici.

---

#### Options avancées

Pour des explications détaillées sur les paramètres supplémentaires de la ligne de commande, veuillez vous référer à [options avancées](./../advanced/advanced.md).

<div align="right"> 
<h6><small>Une partie du contenu de cette page a été traduite par GPT et peut contenir des erreurs.</small></h6>