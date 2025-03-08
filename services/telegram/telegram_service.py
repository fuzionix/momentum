from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from services.data.yahoo_service import YahooFinanceService
from services.llm.replicate_service import ReplicateService
from services.utils.validation import Validation

class TelegramService:
    def __init__(self, token: str):
        self.application = Application.builder().token(token).build()
        self.yahoo_service = YahooFinanceService()
        self.replicate_service = ReplicateService()
        self.validation = Validation()

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [InlineKeyboardButton("🎯 Analyze Stock", callback_data="analyze_stock")],
            [InlineKeyboardButton("⚫ About Momentum", callback_data="about_bot")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            text="I deliver comprehensive financial analysis powered by AI reasoning model.",
            reply_markup=reply_markup
        )

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        if query.data == "about_bot":
            about_text = (
                "Momentum Financial Bot\n\n"
                "Momentum provides professional financial insights powered by latest reasoning model.\n\n"
                "Features:\n"
                "• Real-time data\n"
                "• Technical analysis indicators\n"
                "• AI-generated insights and recommendations\n"
                "• Risk assessments and key metrics\n\n"
            )
            
            await query.message.reply_text(
                text=about_text,
                parse_mode="HTML",
            )
            
        elif query.data == "analyze_stock":
            await query.message.reply_text(
                text="Please use /ticker with stock ticker symbol (e.g., /ticker AAPL)",
            )

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
        self.application.add_handler(
            CallbackQueryHandler(self.button_callback))

    def run(self):
        self.application.run_polling()
