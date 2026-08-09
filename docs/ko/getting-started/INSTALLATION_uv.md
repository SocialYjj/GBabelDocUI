# uv로 GBabelDocUI 설치

필요한 검증된 pdf2zh-next 런타임 일부가 이미 포함되어 있습니다. 업스트림 CLI를 `gbabeldocui` 대신 사용하지 마십시오.

## 요구 사항

- Python 3.10–3.13
- Git
- [uv](https://docs.astral.sh/uv/getting-started/installation/)

## 설치 및 실행

```bash
git clone https://github.com/SocialYjj/GBabelDocUI.git
cd GBabelDocUI
uv sync --frozen
```

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

시작 후 `http://127.0.0.1:7860/login.html`을 여십시오.

공개 배포에서는 Secure 쿠키를 유지하고 HTTPS와 데이터 디렉터리당 하나의 인스턴스를 사용하십시오.

## 개발 환경

```bash
uv sync --dev --frozen
uv run pytest -q
uv run ruff check gbabeldocui tests
uv run ruff format --check gbabeldocui tests
```
