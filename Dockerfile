FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim@sha256:531f855bda2c73cd6ef67d56b733b357cea384185b3022bd09f05e002cd144ca AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

COPY pyproject.toml uv.lock README.md LICENSE NOTICE ./
COPY gbabeldocui ./gbabeldocui

RUN uv sync --frozen --no-dev --no-editable


FROM python:3.13-slim-bookworm@sha256:67a1e1f215ccda113cfc024e8639049257e88f273898f595b61476d128d387e8 AS runtime

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        libgl1 \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender1 \
        tini \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --gid 10001 gbabeldocui \
    && useradd --uid 10001 --gid 10001 --create-home --shell /usr/sbin/nologin gbabeldocui \
    && mkdir -p /app/data /cache \
    && chown -R 10001:10001 /app /cache /home/gbabeldocui

WORKDIR /app

COPY --from=builder --chown=10001:10001 /app/.venv /app/.venv

ENV HOME=/home/gbabeldocui \
    PATH=/app/.venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    XDG_CACHE_HOME=/cache \
    HF_HOME=/cache/huggingface \
    TMPDIR=/tmp

EXPOSE 7860

USER 10001:10001

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:7860/api/auth/status', timeout=3); urllib.request.urlopen('http://127.0.0.1:7860/login.html', timeout=3)"

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["gbabeldocui"]
