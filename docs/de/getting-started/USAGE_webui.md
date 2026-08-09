# GBabelDocUI-Weboberfläche verwenden

Der Dienst öffnet keinen Browser automatisch. Starten Sie ihn und rufen Sie die Anmeldeseite manuell auf.

## Voraussetzungen

- Python 3.10–3.13
- Git
- [uv](https://docs.astral.sh/uv/)

## Aus dem Repository starten

```bash
git clone https://github.com/SocialYjj/GBabelDocUI.git
cd GBabelDocUI
uv sync --frozen
```

Für lokales HTTP muss das Secure-Attribut des Cookies deaktiviert werden:

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

Öffnen Sie anschließend `http://127.0.0.1:7860/login.html`.

## Erste Verwendung

1. Erstellen Sie den ersten Administrator über die lokale Anmeldeseite.
2. Konfigurieren Sie OpenAI, Azure OpenAI oder Google Gemini unter Einstellungen.
3. Wählen Sie Sprachen, Ausgabe, Seitenbereich und PDF-Optionen.
4. Laden Sie ein PDF hoch, starten Sie die Aufgabe und laden Sie das Ergebnis aus dem Verlauf herunter.

Gespeicherte API-Schlüssel bleiben serverseitig. Das Verzeichnis `data/` darf nicht eingecheckt oder veröffentlicht werden.

Für Container verwenden Sie die Docker-Compose-Anleitung. Öffentliche Bereitstellungen benötigen HTTPS und genau eine Instanz pro Datenverzeichnis.
