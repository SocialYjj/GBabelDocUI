> This locale currently uses the canonical English text to avoid publishing outdated translated instructions.

# Internal HTTP API

GBabelDocUI does not currently publish a stable external HTTP API contract. Routes under `/api/` are the authenticated interface used by the bundled Web UI and may change with the frontend.

Authentication uses `HttpOnly` session cookies plus a CSRF cookie/header pair. Bearer tokens and browser `localStorage` sessions are not supported. Do not bypass the Web UI security boundary or expose selected internal routes without the same authentication, CSRF, request-size, and origin controls.
