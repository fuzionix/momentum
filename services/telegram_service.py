from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from services.yahoo_service import YahooFinanceService
from services.replicate_service import ReplicateService
from services.validation_service import ValidationService

class TelegramService:
    def __init__(self, token: str):
        self.application = Application.builder().token(token).build()
        self.yahoo_service = YahooFinanceService()
        self.replicate_service = ReplicateService()
        self.validation = ValidationService()

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Welcome to Momentum! Please use /ticker SYMBOL to get financial insights")

    async def ticker_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            message = self.validation.format_telegram_message(
                "Please provide a ticker symbol! Example: /ticker AAPL"
            )
            await update.message.reply_text(
                text=message,
                parse_mode="MarkdownV2"
            )
            return

        ticker_symbol = context.args[0].upper()

        # Validate ticker symbol
        is_valid, error_message = self.validation.validate_ticker(ticker_symbol)
        if not is_valid:
            message = self.validation.format_telegram_message(
                f"{error_message}. Please try again with a valid symbol."
            )
            await update.message.reply_text(
                text=message,
                parse_mode="MarkdownV2"
            )
            return

        message = self.validation.format_telegram_message(
            f"Analyzing {ticker_symbol}..."
        )
        await update.message.reply_text(
            text=message,
            parse_mode="MarkdownV2"
        )

        stock_data = self.yahoo_service.get_stock_data(ticker_symbol)

        insights = self.replicate_service.get_financial_insight(stock_data)
        await update.message.reply_text(
            text=insights,
            parse_mode="HTML"
        )

    def setup(self):
        self.application.add_handler(
            CommandHandler("start", self.start_command))
        self.application.add_handler(
            CommandHandler("ticker", self.ticker_command))

    def run(self):
        self.application.run_polling()
