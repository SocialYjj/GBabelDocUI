# GBabelDocUI

GBabelDocUI는 BabelDOC 기반의 자체 호스팅 다중 사용자 PDF 번역 Web UI입니다.

이 프로젝트는 eaiu/GBabelDocUI를 기반으로 하며 검증된 pdf2zh-next 2.9.0 런타임 일부를 포함합니다. 업스트림 CLI, Gradio UI 및 HTTP API는 포함하지 않습니다.

## 주요 기능

- 사용자별로 분리된 계정, 설정, 파일, 작업 및 기록.
- HttpOnly 쿠키, CSRF 보호, 로그인 제한 및 세션 상한.
- PDF 내용, 크기, 페이지, 저장소 할당량 및 동시 작업 검증.
- OpenAI, Azure OpenAI 및 Google Gemini Web 설정.
- SQLite 영속성과 단일 인스턴스용 보안 강화 Docker Compose.

## 빠른 시작

### Docker Compose

```bash
git clone https://github.com/SocialYjj/GBabelDocUI.git
cd GBabelDocUI
mkdir -p data
sudo chown -R 10001:10001 data  # Linux bind mounts only
docker compose up -d --build
```

### uv

```bash
git clone https://github.com/SocialYjj/GBabelDocUI.git
cd GBabelDocUI
uv sync --frozen
export GBABELDOCUI_COOKIE_SECURE=false
uv run gbabeldocui
```

시작 후 `http://127.0.0.1:7860/login.html`을 여십시오.

## 배포 제한

- 공개 접근에는 HTTPS 리버스 프록시와 `GBABELDOCUI_COOKIE_SECURE=true`가 필요합니다.
- 첫 관리자는 로컬에서 생성합니다. 원격 초기화에는 일회용 `GBABELDOCUI_SETUP_TOKEN`이 필요합니다.
- 데이터 디렉터리마다 애플리케이션 프로세스와 복제본은 하나만 실행합니다.
- `data/`에는 계정, API 키, PDF 및 결과가 포함될 수 있으므로 공개하지 마십시오.

## 문서

- [Docker](./getting-started/INSTALLATION_docker.md)
- [uv](./getting-started/INSTALLATION_uv.md)
- [Web UI](./getting-started/USAGE_webui.md)
- [Advanced reference](./advanced/advanced.md)

## 소스 및 라이선스

GBabelDocUI와 포함된 런타임은 AGPL-3.0으로 배포됩니다. 출처, 체크섬 및 수정 범위는 NOTICE와 UPSTREAM.md에 기록되어 있습니다.

- [AGPL-3.0](https://github.com/SocialYjj/GBabelDocUI/blob/main/LICENSE)
- [NOTICE](https://github.com/SocialYjj/GBabelDocUI/blob/main/NOTICE)
- [UPSTREAM.md](https://github.com/SocialYjj/GBabelDocUI/blob/main/gbabeldocui/_vendor/pdf2zh_next/UPSTREAM.md)
