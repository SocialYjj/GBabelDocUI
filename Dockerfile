FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app


EXPOSE 7860

ENV PYTHONUNBUFFERED=1

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:7860/api/auth/status', timeout=3); urllib.request.urlopen('http://127.0.0.1:7860/login.html', timeout=3)"

# # Download all required fonts
# ADD "https://github.com/satbyy/go-noto-universal/releases/download/v7.0/GoNotoKurrent-Regular.ttf" /app/
# ADD "https://github.com/timelic/source-han-serif/releases/download/main/SourceHanSerifCN-Regular.ttf" /app/
# ADD "https://github.com/timelic/source-han-serif/releases/download/main/SourceHanSerifTW-Regular.ttf" /app/
# ADD "https://github.com/timelic/source-han-serif/releases/download/main/SourceHanSerifJP-Regular.ttf" /app/
# ADD "https://github.com/timelic/source-han-serif/releases/download/main/SourceHanSerifKR-Regular.ttf" /app/

RUN apt-get update && \
     apt-get install --no-install-recommends -y libgl1 libglib2.0-0 libxext6 libsm6 libxrender1 && \
     rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./
RUN apt-get update && \
    apt-get install --no-install-recommends -y build-essential && \
    uv export --frozen --no-dev --no-emit-project --format requirements.txt --output-file /tmp/requirements.txt && \
    uv pip install --system --no-cache -r /tmp/requirements.txt && \
    apt-get purge -y --auto-remove build-essential && \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

COPY . .

RUN uv pip install --system --no-cache --no-deps . && \
    babeldoc --version && \
    pdf2zh --version
CMD ["gbabeldocui"]
