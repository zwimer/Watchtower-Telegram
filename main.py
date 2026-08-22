from asyncio import create_task, to_thread
from typing import TYPE_CHECKING
from threading import Lock
import argparse
import logging
import os

from telegram.ext import Application, CommandHandler, MessageHandler, filters
import requests

if TYPE_CHECKING:
    from telegram.ext import ContextTypes
    from telegram import Update


LOG_NAME = "watchtower-telegram"


class Watchtower:

    __slots__ = ("_count", "_lock", "_token", "_url")

    def __init__(self, watchtower_url: str, token: str) -> None:
        self._count = 0  # For user message clarity
        self._lock = Lock()
        self._token = token
        self._url = f"{watchtower_url}/v1/update"

    async def update(self, update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        """curl -H "Authorization: Bearer <token>" <host>/v1/update"""
        log = logging.getLogger(LOG_NAME)
        try:
            with self._lock:  # Don't want concurrent updates
                # Log the action
                uid = self._count
                self._count += 1
                log.debug("Starting update uid=%d", uid)
                # Tell the user ACK, no need to wait on this
                _ = create_task(update.message.reply_text(f"Initiating update {uid}"))
                # Tell watchtower to update
                data = {"Authorization": f"Bearer {self._token}"}
                log.info("Making request to %s with headers=%s", self._url, data)
                r = await to_thread(requests.post, self._url, headers=data, timeout=300)
            log.debug("Response: %s", r.text)
            r.raise_for_status()
        except requests.exceptions.RequestException:
            log.exception("Update uid=%d failed", uid)
            await update.message.reply_text(f"Update {uid} failed")
        await update.message.reply_text(f"Update {uid} complete")


async def help_cmd(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("/update To update containers")


def main() -> None:
    url_var: str = "WATCHTOWER_URL"
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--url", default="http://localhost:8080", help=f"The watchtower host; overridden by {url_var}"
    )
    parser.add_argument(
        "--log-level",
        default="WARNING",
        choices=("DEBUG", "INFO", "WARNING", "ERROR"),
        help="The log level to use",
    )
    ns = parser.parse_args()
    # Log config
    logging.basicConfig(level=logging.WARNING)
    level = ns.log_level.upper()
    log = logging.getLogger(LOG_NAME)
    log.setLevel(logging.getLevelName(level))
    log.info("Log level set to: %s", level)
    # App config
    watchtower = Watchtower(os.environ.get(url_var, f"{ns.url}"), os.environ["WATCHTOWER_HTTP_API_TOKEN"])
    app = Application.builder().token(os.environ["WATCHTOWER_TELEGRAM_TOKEN"]).build()
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("start", help_cmd))
    app.add_handler(CommandHandler("update", watchtower.update))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, help_cmd))
    app.run_polling()


if __name__ == "__main__":
    main()
