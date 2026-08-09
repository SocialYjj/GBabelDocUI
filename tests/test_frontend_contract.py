import re
from pathlib import Path

STATIC_DIR = Path(__file__).resolve().parents[1] / "gbabeldocui" / "static"


def static_text_files():
    yield from STATIC_DIR.glob("*.html")
    yield from (STATIC_DIR / "js").glob("*.js")
    yield from (STATIC_DIR / "css").glob("*.css")


def test_frontend_has_no_browser_stored_session_or_bearer_header():
    combined_source = "\n".join(
        path.read_text(encoding="utf-8") for path in static_text_files()
    )

    assert "auth_token" not in combined_source
    assert "user_info" not in combined_source
    assert "Authorization" not in combined_source
    assert "Bearer " not in combined_source
    assert "gbabeldocui_session" not in combined_source


def test_frontend_uses_csrf_and_same_origin_credentials():
    api_source = (STATIC_DIR / "js" / "api.js").read_text(encoding="utf-8")

    assert "gbabeldocui_csrf" in api_source
    assert "X-CSRF-Token" in api_source
    assert "credentials: 'same-origin'" in api_source
    assert "withCredentials = true" in api_source


def test_html_has_no_inline_scripts_or_external_asset_dependencies():
    for html_file in STATIC_DIR.glob("*.html"):
        html_source = html_file.read_text(encoding="utf-8")
        assert not re.search(r"<script(?![^>]*\bsrc=)[^>]*>", html_source, re.I)
        assert "fonts.googleapis.com" not in html_source
        assert "fonts.gstatic.com" not in html_source
        assert "cdnjs.cloudflare.com" not in html_source


def test_dynamic_markup_avoids_string_html_and_inline_click_actions():
    combined_source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [*STATIC_DIR.glob("*.html"), *(STATIC_DIR / "js").glob("*.js")]
    )

    assert "innerHTML" not in combined_source
    assert "onclick=" not in combined_source
    assert "console.log" not in combined_source


def test_settings_page_exposes_only_fully_supported_providers():
    settings_source = (STATIC_DIR / "settings.html").read_text(encoding="utf-8")
    service_select = re.search(
        r'<select class="form-select" id="service">(.*?)</select>',
        settings_source,
        re.S,
    )
    assert service_select
    provider_values = re.findall(r'<option value="([^"]+)"', service_select.group(1))

    assert provider_values == ["OpenAI", "AzureOpenAI", "GoogleGemini"]
