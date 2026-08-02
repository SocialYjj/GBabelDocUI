import os

import uvicorn

from gbabeldocui.web_api import app


def cli() -> None:
    port = int(os.getenv("PORT", os.getenv("PDF2ZH_SERVER_PORT", "7860")))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")


if __name__ == "__main__":
    cli()
