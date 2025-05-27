import os
from dotenv import load_dotenv
load_dotenv()

class Settings:
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN")
    WEBAPP_URL: str = os.getenv("WEBAPP_URL")
    DATABASE_URL: str = os.getenv("DATABASE_URL")

settings = Settings()
