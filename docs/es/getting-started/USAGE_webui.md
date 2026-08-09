# Usar la interfaz web de GBabelDocUI

El servicio no abre el navegador automáticamente. Inícielo y abra manualmente la página de acceso.

## Requisitos

- Python 3.10–3.13
- Git
- [uv](https://docs.astral.sh/uv/)

## Ejecutar desde el repositorio

```bash
git clone https://github.com/SocialYjj/GBabelDocUI.git
cd GBabelDocUI
uv sync --frozen
```

Para HTTP local, desactive el atributo Secure de la cookie:

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

Después, abra `http://127.0.0.1:7860/login.html`.

## Primer uso

1. Cree el primer administrador desde la página de acceso local.
2. Configure OpenAI, Azure OpenAI o Google Gemini en Ajustes.
3. Seleccione idiomas, salida, intervalo de páginas y opciones PDF.
4. Suba un PDF, inicie la tarea y descargue el resultado desde el historial.

Las claves API guardadas permanecen en el servidor. No confirme ni publique el directorio `data/`.

Para contenedores, use la guía de Docker Compose. Los despliegues públicos requieren HTTPS y una sola instancia por directorio de datos.
