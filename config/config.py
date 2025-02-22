import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
REPLICATE_TOKEN = os.getenv('REPLICATE_API_TOKEN')