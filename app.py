from flask import Flask
from services.telegram_service import TelegramService
from config.config import TELEGRAM_TOKEN

app = Flask(__name__)
telegram_service = TelegramService(TELEGRAM_TOKEN)

@app.route('/')
def home():
    return "Ticker Bot is running!"

def main():
    print("Bot is running!")
    telegram_service.setup()
    telegram_service.run()

if __name__ == '__main__':
    main()