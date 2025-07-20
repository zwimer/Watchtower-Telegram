from __future__ import annotations
from typing import TYPE_CHECKING
import argparse
import logging
import os

from telegram.ext import Application, CommandHandler, MessageHandler, filters
import requests

if TYPE_CHECKING:
    from telegram.ext import ContextTypes
    from telegram import Update


# Pass by env instead of CLI for security
T_TOKEN_VAR: str = "WATCHTOWER_TELEGRAM_TOKEN"
W_TOKEN_VAR: str = "WATCHTOWER_HTTP_API_TOKEN"


class Watchtower:

    def __init__(self, watchtower_url: str, token: str) -> None:
        self._url: str = f"{watchtower_url}/v1/update"
        self._token: str = token

    async def update(self, _: Update, __: ContextTypes.DEFAULT_TYPE) -> None:
        """
        curl -H "Authorization: Bearer <token>" <host>/v1/update
        """
        if not self._url or not self._token:
            raise RuntimeError("init not called")
        data = {"Authorization": f"Bearer {self._token}"}
        logging.info("Making request to %s with headers=%s", self._url, data)
        r = requests.get(self._url, headers=data)
        logging.debug("Response: %s", r.text)
        r.raise_for_status()


async def help_cmd(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("/update To update containers")


def main() -> None:

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="localhost", help="The watchtower host")
    parser.add_argument("--port", default="8080", help="The watchtower port")
    parser.add_argument(
        "--protocol",
        default="http",
        choices=["http", "https"],
        help="The watchtower protocol",
    )
    parser.add_argument("--log-level", default="WARNING", help="The log level to use")
    ns = parser.parse_args()

    watchtower = Watchtower(
        f"{ns.protocol}://{ns.host}:{ns.port}", os.environ[W_TOKEN_VAR]
    )
    logging.basicConfig(level=logging.getLevelName(ns.log_level.upper()))

    app = Application.builder().token(os.environ[T_TOKEN_VAR]).build()
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("start", help_cmd))
    app.add_handler(CommandHandler("update", watchtower.update))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, help_cmd))
    app.run_polling()


if __name__ == "__main__":
    main()
