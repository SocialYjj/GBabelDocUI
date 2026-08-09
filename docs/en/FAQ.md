# Frequently asked questions

## Why did the browser not open automatically?

`gbabeldocui` starts the server but does not launch a browser. Open `http://127.0.0.1:7860/login.html` manually.

## Why does local HTTP return to the login page?

Secure cookies are enabled by default. For loopback HTTP only, set `GBABELDOCUI_COOKIE_SECURE=false` before starting the service. Public deployments must use HTTPS and keep the value `true`.

## Why can I not create the first administrator remotely?

Local setup is the default security boundary. For a trusted remote initialization, set a one-time high-entropy `GBABELDOCUI_SETUP_TOKEN`, complete setup, then remove the variable and restart the service.

## Can several workers or containers share one data directory?

No. The application intentionally allows one process and one replica per `data/` directory. A second instance fails fast instead of corrupting task state.

## What happens after a restart?

Task state and history are stored in SQLite. Incomplete tasks are reconciled during startup; completed, failed, and cancelled records follow the configured retention policy.

## Why is an API-key field empty after reloading settings?

Saved keys are never returned to the browser. Leave the field empty to keep the existing key, or enter a new value to replace it.

## Where are uploads and results stored?

They are stored under the configured `GBABELDOCUI_DATA_DIR`, normally `data/users/<username>/`. This directory can contain credentials and private documents and must not be committed or published.

## How do I update?

For a source installation, use `git pull --ff-only`, then `uv sync --frozen`. For Compose, pull the source update and run `docker compose up -d --build`. Back up the protected data directory while the service is stopped before a major operational change.

## Why was an upload rejected with HTTP 413?

The request exceeded `GBABELDOCUI_MAX_UPLOAD_BYTES` or the streaming request-body limit. Raising the limit also increases storage and processing exposure; keep it bounded for public deployments.
