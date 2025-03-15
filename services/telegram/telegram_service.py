from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from utils.validation import Validation
from services.database.db_service import DatabaseService
from services.data.yahoo_service import YahooFinanceService
from services.llm.replicate_service import ReplicateService

class TelegramService:
    def __init__(self, token: str, db_service: DatabaseService):
        self.application = Application.builder().token(token).build()
        self.yahoo_service = YahooFinanceService()
        self.replicate_service = ReplicateService()
        self.validation = Validation()
        self.db_service = db_service

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        self.db_service.get_or_create_user(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            language=user.language_code
        )

        await self.render_home_page(update.message)

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        user = update.effective_user
        telegram_id = user.id
        
        if query.data == 'go_home':
            await self.render_home_page(query.message)

        elif query.data == 'about_bot':
            about_text = (
                'Momentum Financial Bot\n\n'
                'This is an experimental project developed by HKBU student - Taylon Chan.\n\n'
                'Momentum provides professional financial insights powered by latest reasoning model.\n\n'
                'Features:\n'
                '• Real-time data\n'
                '• Technical analysis indicators\n'
                '• AI-generated insights and recommendations\n'
                '• Risk assessments and key metrics\n\n'
                '<a href="https://github.com/fuzionix/momentum">GitHub</a>'
            )
            
            await query.message.reply_text(
                text=about_text,
                parse_mode='HTML',
            )
            
        elif query.data == 'analyze_stock':
            context.user_data['awaiting_ticker'] = {
                'mode': 'analyze_stock'
            }
            await query.message.reply_text(
                text='Please enter the stock ticker symbol. E.g. AAPL',
            )

        elif query.data == "check_credits":
            await self.send_credit_info(query.message, telegram_id)

    async def render_home_page(self, message):
        keyboard = [
            [
                InlineKeyboardButton('🎯 Analyze Stock', callback_data='analyze_stock'), 
                InlineKeyboardButton('🪙 Check Credits', callback_data='check_credits')
            ],
            [InlineKeyboardButton('⚫ About Momentum', callback_data='about_bot')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await message.reply_text(
            text='Momentum deliver comprehensive financial analysis powered by AI reasoning model.',
            reply_markup=reply_markup
        )
            
    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        '''Handle messages based on previous context'''
        user = update.effective_user
        message_text = update.message.text

        awaiting_ticker = context.user_data.get('awaiting_ticker')
        if awaiting_ticker and awaiting_ticker.get('mode') == 'analyze_stock':
            context.user_data['awaiting_ticker'] = {
                'mode': 'idle'
            }

            db_user = self.db_service.get_or_create_user(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                language=user.language_code
            )
            await self.process_ticker(update, context, message_text, db_user)
            return
        
    async def process_ticker(self, update: Update, context: ContextTypes.DEFAULT_TYPE, ticker_symbol: str, db_user: dict):
        '''Process ticker symbol (extracted for reuse)'''
        ticker_symbol = ticker_symbol.upper()
        
        # Validate ticker symbol
        is_valid, error_message = self.validation.validate_ticker(ticker_symbol)
        if not is_valid:
            message = self.validation.format_telegram_message(
                f'{error_message}. Please try again with a valid symbol.'
            )
            await update.message.reply_text(
                text=message,
                parse_mode='MarkdownV2'
            )
            # Set context again so next message is treated as a ticker attempt
            context.user_data['awaiting_ticker'] = {
                'mode': 'analyze_stock'
            }
            return

        message = self.validation.format_telegram_message(
            f'Analyzing {ticker_symbol}'
        )
        loading_message = await update.message.reply_text(
            text=message,
            parse_mode='MarkdownV2'
        )

        stock_data = self.yahoo_service.get_stock_data(ticker_symbol)
        insights, replicate_id = self.replicate_service.get_financial_insight(stock_data)

        self.db_service.log_analysis(
            user_id=db_user['id'],
            ticker_symbol=ticker_symbol,
            replicate_id=replicate_id
        )

        await loading_message.delete()

        keyboard = [
            [InlineKeyboardButton('🏠 Home Page', callback_data='go_home')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            text=insights,
            parse_mode='HTML',
            reply_markup=reply_markup
        )

    async def send_credit_info(self, message, telegram_id):
        """Send credit information to the user"""
        credit_info = self.db_service.get_credits_info(telegram_id)
        credits = credit_info['credits']
        next_reset = credit_info['next_reset']
        
        # Format time until reset
        time_until_reset = next_reset - datetime.now()
        hours = int(time_until_reset.total_seconds() // 3600)
        minutes = int((time_until_reset.total_seconds() % 3600) // 60)
        
        credit_emoji = "🟢" if credits >= 3 else "🟡" if credits > 0 else "🔴"
        credit_text = (
            f"<b>Your Credits: {credits} {credit_emoji}</b>\n\n"
            f"• Each analysis costs 1 credit\n"
            f"• Credits renew to at least 3 every 24 hours\n"
            f"• Next reset in approximately {hours}h {minutes}m\n\n"
        )
        
        if credits <= 0:
            credit_text += "⚠️ You're out of credits! Please wait for renewal."
        elif credits == 1:
            credit_text += "⚠️ You have just 1 credit left! Use it wisely."
        
        await message.reply_text(
            text=credit_text,
            parse_mode="HTML",
        )

    def setup(self):
        self.application.add_handler(CommandHandler('start', self.start_command))
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.message_handler))

    def run(self):
        self.application.run_polling()
