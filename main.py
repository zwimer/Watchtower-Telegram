from asyncio import create_task, to_thread
from typing import TYPE_CHECKING
from threading import Lock
import argparse
import logging
import random
import string
import os

from telegram.ext import Application, CommandHandler, MessageHandler, filters
import requests

if TYPE_CHECKING:
    from telegram.ext import ContextTypes
    from telegram import Update


CHARSET = string.ascii_lowercase + string.ascii_uppercase + string.digits
LOG_NAME = "watchtower-telegram"


class Watchtower:

    __slots__ = ("_headers", "_lock", "_url")

    def __init__(self, watchtower_url: str, token: str) -> None:
        random.seed(int.from_bytes(os.urandom(4)))
        self._headers = {"Authorization": f"Bearer {token}"}
        self._url = f"{watchtower_url}/v1/update"
        self._lock = Lock()

    async def update(self, update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        """curl -H "Authorization: Bearer <token>" <host>/v1/update"""
        prefix = f"Update[id={"".join(random.choices(CHARSET, k=6))}]: "  # noqa: S311
        log = logging.getLogger(LOG_NAME)
        try:
            with self._lock:  # Avoid concurrent updates
                msg = f"{prefix}Starting"
                log.debug("%s", msg)
                _ = create_task(update.message.reply_text(msg))
                log.info("%sMaking request to %s with headers=%s", prefix, self._url, self._headers)
                r = await to_thread(requests.post, self._url, headers=self._headers, timeout=300)
            log.debug("%sResponse: %s", prefix, r.text)
            r.raise_for_status()
        except requests.exceptions.RequestException:
            msg = f"{prefix}Failed"
            log.exception("%s", msg)
            await update.message.reply_text(msg)
        await update.message.reply_text(f"{prefix}Complete")


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
