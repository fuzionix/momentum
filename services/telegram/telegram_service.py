from typing import Dict
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand, MenuButtonCommands
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from utils.validation import Validation
from services.database.db_service import DatabaseService
from services.data.yahoo_service import YahooFinanceService
from services.llm.replicate_service import ReplicateService
from localization.translator import Translator

class TelegramService:
    def __init__(self, token: str, db_service: DatabaseService):
        self.application = Application.builder().token(token).build()
        self.yahoo_service = YahooFinanceService()
        self.replicate_service = ReplicateService()
        self.validation = Validation()
        self.db_service = db_service
        self.translator = Translator

    async def setup_chat_menu(self):        
        commands = [
            BotCommand('analyze', 'Analyze a stock'),
            BotCommand('credits', 'Check remaining credits'),
        ]
        
        await self.application.bot.set_my_commands(commands)
        await self.application.bot.set_chat_menu_button(menu_button=MenuButtonCommands())

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

    async def analyze_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.analyze_stock(update, context)

    async def credits_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.check_credits(update)

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
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
            await self.analyze_stock(update, context)

        elif query.data == "check_credits":
            await self.check_credits(update)

    async def render_home_page(self, message):
        keyboard = [
            [
                InlineKeyboardButton('Analyze Stock', callback_data='analyze_stock'), 
                InlineKeyboardButton('Check Credits', callback_data='check_credits'),
            ],
            [
                InlineKeyboardButton('How To Use', callback_data='tutorial'),
            ],
            [
                InlineKeyboardButton('About Momentum', callback_data='about_bot')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await message.reply_text(
            text='Momentum deliver comprehensive financial analysis powered by AI reasoning model.',
            reply_markup=reply_markup
        )

    async def render_out_of_credits(self, message, telegram_id):
        credit_info = self.db_service.get_credits_info(telegram_id)
        next_reset = credit_info['next_reset']

        time_until_reset = next_reset - datetime.now()
        hours = int(time_until_reset.total_seconds() // 3600)
        minutes = int((time_until_reset.total_seconds() % 3600) // 60)

        await message.reply_text(
            text=f"⚠️ You're out of credits! \n\nCredits will renew in approximately {hours}h {minutes}m.",
            parse_mode="HTML",
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
        
    async def process_ticker(self, update: Update, context: ContextTypes.DEFAULT_TYPE, ticker_symbol: str, db_user: Dict):
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
            f'Analyzing {ticker_symbol} ...'
        )
        loading_message = await update.message.reply_text(
            text=message,
            parse_mode='MarkdownV2'
        )

        stock_data = self.yahoo_service.get_stock_data(ticker_symbol)
        if 'error' in stock_data:
            await loading_message.delete()
            error_msg = f"❌ Error retrieving stock data. Please try again with a valid ticker symbol."
            context.user_data['awaiting_ticker'] = {
                'mode': 'analyze_stock'
            }
            await update.message.reply_text(
                text=error_msg,
            )
            return
        
        success, credits_left = self.db_service.use_credit(db_user.get('telegram_id'))
        if not success:
            await self.render_out_of_credits(update.message, db_user.get('telegram_id'))
            return
        
        insights, replicate_id = self.replicate_service.get_financial_insight(stock_data)

        self.db_service.log_analysis(
            user_id=db_user['id'],
            ticker_symbol=ticker_symbol,
            replicate_id=replicate_id
        )

        await loading_message.delete()

        keyboard = [
            [InlineKeyboardButton('Home Page', callback_data='go_home')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            text=insights,
            parse_mode='HTML',
            reply_markup=reply_markup
        )

    async def check_credits(self, update: Update):
        """Send credit information to the user"""
        user = update.effective_user
        telegram_id = user.id

        message = update.message
        if message is None and update.callback_query:
            message = update.callback_query.message

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

    async def analyze_stock(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Analyze stock command"""
        user = update.effective_user
        telegram_id = user.id

        message = update.message
        if message is None and update.callback_query:
            message = update.callback_query.message

        credits = self.db_service.get_user_credits(telegram_id)
        if credits <= 0:
            await self.render_out_of_credits(message, telegram_id)
            return

        context.user_data['awaiting_ticker'] = {
            'mode': 'analyze_stock'
        }
        await message.reply_text(
            text='Please enter the stock ticker symbol. E.g. NVDA',
        )

    def setup(self):
        self.application.add_handler(CommandHandler('start', self.start_command))
        self.application.add_handler(CommandHandler('analyze', self.analyze_command))
        self.application.add_handler(CommandHandler('credits', self.credits_command))
        
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.message_handler))

    def run(self):
        # self.setup_chat_menu()
        self.application.run_polling()
