from typing import TYPE_CHECKING
import argparse
import logging
import os

from telegram.ext import Application, CommandHandler, MessageHandler, filters
import requests

if TYPE_CHECKING:
    from telegram.ext import ContextTypes
    from telegram import Update


class Watchtower:

    __slots__ = ("_lock", "_log", "_token", "_url")

    def __init__(self, watchtower_url: str, token: str) -> None:
        self._url: str = f"{watchtower_url}/v1/update"
        self._token: str = token

    async def update(self, _: Update, __: ContextTypes.DEFAULT_TYPE) -> None:
        """
        curl -H "Authorization: Bearer <token>" <host>/v1/update
        """
        log = logging.getLogger("main")
        data = {"Authorization": f"Bearer {self._token}"}
        log.info("Making request to %s with headers=%s", self._url, data)
        r = requests.post(self._url, headers=data, timeout=300)  # noqa: ASYNC210 (blocking is ok)
        log.debug("Response: %s", r.text)
        r.raise_for_status()


async def help_cmd(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("/update To update containers")


def main() -> None:
    url_var: str = "WATCHTOWER_URL"
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--url", default="http://localhost:8080", help=f"The watchtower host; overridden by {url_var}"
    )
    parser.add_argument("--log-level", default="WARNING", help="The log level to use")
    ns = parser.parse_args()

    watchtower = Watchtower(os.environ.get(url_var, f"{ns.url}"), os.environ["WATCHTOWER_HTTP_API_TOKEN"])
    logging.basicConfig(level=logging.getLevelName(ns.log_level.upper()))

    app = Application.builder().token(os.environ["WATCHTOWER_TELEGRAM_TOKEN"]).build()
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("start", help_cmd))
    app.add_handler(CommandHandler("update", watchtower.update))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, help_cmd))
    app.run_polling()


if __name__ == "__main__":
    main()
