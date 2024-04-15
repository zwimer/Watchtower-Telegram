from __future__ import annotations
from typing import TYPE_CHECKING
import logging
import os

from telegram.ext import Application, CommandHandler, MessageHandler, filters
import requests

if TYPE_CHECKING:
    from telegram.ext import ContextTypes
    from telegram import Update


host: str = "http://localhost:8080"
t_var: str = "WATCHTOWER_TELEGRAM_TOKEN"
w_var: str = "WATCHTOWER_HTTP_API_TOKEN"


async def do_update(_: Update, __: ContextTypes.DEFAULT_TYPE) -> None:
    # curl -H "Authorization: Bearer <token>" <host>/v1/update
    url = f"{host}/v1/update"
    data = {"Authorization": f"Bearer {os.environ[w_var]}"}
    logging.info(f"Making request to {url} with headers={data}")
    r = requests.get(url, headers=data)
    logging.info(f"Response: {r.text}")
    r.raise_for_status()


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("/update To update containers")


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    app = Application.builder().token(os.environ[t_var]).build()

    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("start", help_cmd))
    app.add_handler(CommandHandler("update", do_update))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, help_cmd))

    app.run_polling()


if __name__ == "__main__":
    main()
