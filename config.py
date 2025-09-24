import os

from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = int(os.getenv('TELEGRAM_CHAT_ID'))

VERSION = os.getenv('VERSION', 'none')
LANGUAGE = os.getenv('LANGUAGE', 'ES').upper()

DEBUG= int(os.getenv('DEBUG', '0'))

TZ = os.getenv('TZ', 'Europe/Madrid')
