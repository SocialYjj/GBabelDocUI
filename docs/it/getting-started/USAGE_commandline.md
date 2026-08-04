[**Iniziare**](./getting-started.md) > **Utilizzo** > **Riga di comando** _(current)_

---

> **Nota sull'ambito:** Questa pagina è un riferimento per l'[interfaccia ufficiale a riga di comando di `pdf2zh-next`](https://github.com/PDFMathTranslate-next/PDFMathTranslate-next). Non documenta la Web UI di GBabelDocUI. Per la Web UI di GBabelDocUI, consulta [`USAGE_webui.md`](./USAGE_webui.md) e le istruzioni Docker. Non sostituire `pdf2zh_next` con `gbabeldocui`: gli argomenti della riga di comando non sono compatibili.

### Utilizzare PDFMathTranslate tramite riga di comando

#### Utilizzo di base

Dopo l'installazione, inserisci questo comando per tradurre il tuo PDF.

```bash
pdf2zh_next document.pdf
```

> [!NOTE]
> 
> Se il tuo percorso contiene spazi, per favore racchiudilo tra virgolette.
> 
> ```bash
> pdf2zh_next "path with spaces/document.pdf"
> ```

Dopo aver eseguito la traduzione, i file vengono generati nella **directory di lavoro corrente**.

> [!TIP]
> **Dov'è la mia "Directory di lavoro corrente"?**
> Prima di inserire un comando nel terminale, potresti vedere un percorso visualizzato nel tuo terminale:
> 
> ```powershell
> PS C:\Users\XXX>
> ```
> 
> Questa directory è la "*Directory di lavoro corrente*."
> 
> Se non c'è un percorso, prova a eseguire questo comando nel terminale:
> 
> ```bash
> pwd
> ```
> 
> Dopo aver eseguito questo comando, verrà visualizzato un percorso. Questo percorso è la "**Directory di lavoro corrente**". I file tradotti appariranno qui.

---

#### Opzioni avanzate

Per spiegazioni dettagliate sui parametri aggiuntivi della riga di comando, fare riferimento a [opzioni avanzate](./../advanced/advanced.md).

<div align="right"> 
<h6><small>Parte del contenuto di questa pagina è stata tradotta da GPT e potrebbe contenere errori.</small></h6>