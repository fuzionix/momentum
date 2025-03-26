from flask import Flask
from config.config import TELEGRAM_TOKEN
from utils.db_init import initialize_database
from services.database.db_service import DatabaseService
from services.telegram.telegram_service import TelegramService

app = Flask(__name__)

initialize_database()

db_service = DatabaseService()
telegram_service = TelegramService(TELEGRAM_TOKEN, db_service)

@app.route('/')
def home():
    return "Momentum Financial Bot is running!"

def main():
    print("Bot is running!")
    telegram_service.setup()
    telegram_service.run()

if __name__ == '__main__':
    try:
        main()
    finally:
        db_service.close()