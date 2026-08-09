# Usare l'interfaccia Web di GBabelDocUI

Il servizio non apre automaticamente il browser. Avviarlo e aprire manualmente la pagina di accesso.

## Requisiti

- Python 3.10–3.13
- Git
- [uv](https://docs.astral.sh/uv/)

## Eseguire dal repository

```bash
git clone https://github.com/SocialYjj/GBabelDocUI.git
cd GBabelDocUI
uv sync --frozen
```

Per HTTP locale, disabilitare l'attributo Secure del cookie:

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

Aprire quindi `http://127.0.0.1:7860/login.html`.

## Primo utilizzo

1. Creare il primo amministratore dalla pagina di accesso locale.
2. Configurare OpenAI, Azure OpenAI o Google Gemini nelle impostazioni.
3. Selezionare lingue, output, intervallo di pagine e opzioni PDF.
4. Caricare un PDF, avviare l'attività e scaricare il risultato dalla cronologia.

Le chiavi API salvate restano sul server. La directory `data/` non deve essere inclusa nei commit o pubblicata.

Per i container usare la guida Docker Compose. Le distribuzioni pubbliche richiedono HTTPS e una sola istanza per directory dati.
