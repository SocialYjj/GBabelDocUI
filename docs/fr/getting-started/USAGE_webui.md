# Utiliser l'interface Web GBabelDocUI

Le service n'ouvre pas automatiquement le navigateur. Démarrez-le puis ouvrez manuellement la page de connexion.

## Prérequis

- Python 3.10–3.13
- Git
- [uv](https://docs.astral.sh/uv/)

## Exécuter depuis le dépôt

```bash
git clone https://github.com/SocialYjj/GBabelDocUI.git
cd GBabelDocUI
uv sync --frozen
```

Pour un accès HTTP local, désactivez l'attribut Secure du cookie :

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

Ouvrez ensuite `http://127.0.0.1:7860/login.html`.

## Première utilisation

1. Créez le premier administrateur depuis la page de connexion locale.
2. Configurez OpenAI, Azure OpenAI ou Google Gemini dans les paramètres.
3. Choisissez les langues, la sortie, les pages et les options PDF.
4. Téléversez un PDF, lancez la tâche et téléchargez le résultat depuis l'historique.

Les clés API enregistrées restent côté serveur. Le répertoire `data/` ne doit être ni validé ni publié.

Pour les conteneurs, utilisez le guide Docker Compose. Un déploiement public exige HTTPS et une seule instance par répertoire de données.
