> This locale currently uses the canonical English text to avoid publishing outdated translated instructions.

# Translation services

The current GBabelDocUI settings page exposes three fully configurable services.

## OpenAI

Required fields are the model and API key. The Base URL defaults to the public OpenAI API and can be changed to a compatible public HTTPS endpoint. Optional fields include timeout, temperature, JSON mode, and reasoning effort.

## Azure OpenAI

Configure the deployment name, API key, Azure endpoint, and API version. Use the resource endpoint, not a complete chat-completions request URL.

## Google Gemini

Configure the model and API key. JSON mode can be enabled when the selected model supports it.

## Credentials and endpoints

- API keys are stored server-side and are not returned by the settings API.
- Leaving a key field empty keeps the saved value; entering a new value replaces it.
- Custom endpoints are checked for scheme, host, DNS resolution, redirects, and private-address boundaries.
- Private endpoints are rejected unless an administrator explicitly enables `GBABELDOCUI_ALLOW_PRIVATE_ENDPOINTS=true` in a trusted deployment.

The backend retains compatibility code for additional upstream translators, but providers without a complete current Web UI configuration are intentionally not offered in the settings page.
