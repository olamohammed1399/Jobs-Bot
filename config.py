import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TELEGRAM_DISABLE_WEB_PAGE_PREVIEW = (
    os.getenv("TELEGRAM_DISABLE_WEB_PAGE_PREVIEW", "true").lower()
    not in {"0", "false", "no"}
)
