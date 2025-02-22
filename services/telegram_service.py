from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from services.yahoo_service import YahooFinanceService
from services.replicate_service import ReplicateService

class TelegramService:
    def __init__(self, token: str):
        self.application = Application.builder().token(token).build()
        self.yahoo_service = YahooFinanceService()
        self.replicate_service = ReplicateService()

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "Welcome to Ticker Bot! Use /ticker SYMBOL to get financial insights."
        )

    async def ticker_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("Please provide a ticker symbol!")
            return

        ticker_symbol = context.args[0].upper()
        await update.message.reply_text(f"Analyzing {ticker_symbol}...")

        stock_data = self.yahoo_service.get_stock_data(ticker_symbol)
        insights = self.replicate_service.get_financial_insight(stock_data)
        await update.message.reply_text(insights)

    def setup(self):
        self.application.add_handler(
            CommandHandler("start", self.start_command))
        self.application.add_handler(
            CommandHandler("ticker", self.ticker_command))

    def run(self):
        self.application.run_polling()
