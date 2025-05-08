import os

from dotenv import load_dotenv


load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_TELEGRAM_ID = os.getenv("ADMIN_TELEGRAM_ID")

DATABASE_NAME = os.getenv("DATABASE_NAME")
GITLAB_WEBHOOKS_TOKEN = os.getenv("GITLAB_WEBHOOKS_TOKEN")
