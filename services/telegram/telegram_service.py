from typing import Dict
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand, MenuButtonCommands
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from utils.validation import Validation
from services.database.db_service import DatabaseService
from services.data.yahoo_service import YahooFinanceService
from services.llm.replicate_service import ReplicateService
from services.data.news_service import NewsService

class TelegramService:
    def __init__(self, token: str, db_service: DatabaseService):
        self.application = Application.builder().token(token).build()
        self.yahoo_service = YahooFinanceService()
        self.replicate_service = ReplicateService()
        self.validation = Validation()
        self.db_service = db_service
        self.news_service = NewsService()

    async def setup_chat_menu(self):        
        commands = [
            BotCommand('analyze', '分析股票'),
            BotCommand('credits', '查看剩餘點數'),
            BotCommand('news', '環球新聞分析'),
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
                'Momentum 財務洞察機器人\n\n'
                '該系統為香港浸會大學學生開發的實驗項目。\n\n'
                'Momentum 提供由最新推理模型驅動的專業財務洞察。\n\n'
                '功能：\n'
                '．即時數據\n'
                '．技術分析指標\n'
                '．推理模型生成的見解和建議\n'
                '．風險評估和關鍵指標\n'
                '．新聞摘要與分析\n\n'
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

        elif query.data == "get_news":
            await self.get_financial_news(update)

    async def render_home_page(self, message):
        keyboard = [
            [
                InlineKeyboardButton('分析股票', callback_data='analyze_stock'), 
                InlineKeyboardButton('環球新聞分析', callback_data='get_news'),
            ],
            [
                InlineKeyboardButton('查看點數', callback_data='check_credits'),
                InlineKeyboardButton('使用指南', callback_data='tutorial'),
            ],
            [
                InlineKeyboardButton('關於 Momentum', callback_data='about_bot')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await message.reply_text(
            text='Momentum 提供由 AI 推理模型驅動的全面財務分析。',
            reply_markup=reply_markup
        )

    async def render_out_of_credits(self, message, telegram_id):
        credit_info = self.db_service.get_credits_info(telegram_id)
        next_reset = credit_info['next_reset']

        time_until_reset = next_reset - datetime.now()
        hours = int(time_until_reset.total_seconds() // 3600)
        minutes = int((time_until_reset.total_seconds() % 3600) // 60)

        await message.reply_text(
            text=f"⚠️ 您的點數已用完！ \n\n點數將在大約 {hours}小時 {minutes}分鐘後更新。",
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
        '''Process ticker symbol for different exchanges'''
        # Validate ticker symbol
        is_valid, error_message = self.validation.validate_ticker(ticker_symbol)
        if not is_valid:
            message = self.validation.format_telegram_message(
                f'{error_message}。請使用有效的股票代碼重試。'
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

        # Format ticker based on its characteristics
        formatted_ticker = self.validation.format_ticker(ticker_symbol)
        
        message = self.validation.format_telegram_message(
            f'正在分析 {formatted_ticker} ...'
        )
        loading_message = await update.message.reply_text(
            text=message,
            parse_mode='MarkdownV2'
        )

        stock_data = self.yahoo_service.get_stock_data(formatted_ticker)
        if 'error' in stock_data:
            await loading_message.delete()
            error_msg = f"❌ 獲取股票數據時出錯。請使用有效的股票代碼重試。"
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
            ticker_symbol=formatted_ticker,
            replicate_id=replicate_id
        )

        await loading_message.delete()

        keyboard = [
            [InlineKeyboardButton('返回首頁', callback_data='go_home')],
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
            f"<b>您的點數：{credits} {credit_emoji}</b>\n\n"
            f"．每次分析消耗 1 點點數\n"
            f"．點數每 24 小時更新回 3 點數\n"
            f"．下次更新約在 {hours} 小時 {minutes} 分鐘後\n\n"
        )
        
        if credits <= 0:
            credit_text += "⚠️ 您的點數已用完！請等待更新。"
        elif credits == 1:
            credit_text += "⚠️ 您只剩下 1 點點數！請謹慎使用。"

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
            text='請輸入股票代碼。例如：NVDA, 0700',
        )

    async def news_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.get_financial_news(update)

    async def get_financial_news(self, update: Update):
        """Fetch and summarize financial news"""
        user = update.effective_user
        telegram_id = user.id

        message = update.message
        if message is None and update.callback_query:
            message = update.callback_query.message

        credits = self.db_service.get_user_credits(telegram_id)
        if credits <= 0:
            await self.render_out_of_credits(message, telegram_id)
            return

        loading_message = await message.reply_text(
            text='正在獲取最新新聞摘要 ...',
        )

        news_articles = self.news_service.get_highlighted_news(limit=5)
        db_user = self.db_service.get_or_create_user(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            language=user.language_code
        )
        
        success, credits_left = self.db_service.use_credit(db_user.get('telegram_id'))
        if not success:
            await loading_message.delete()
            await self.render_out_of_credits(message, db_user.get('telegram_id'))
            return

        summary, replicate_id = self.replicate_service.summarize_news(news_articles)

        await loading_message.delete()

        keyboard = [
            [InlineKeyboardButton('返回首頁', callback_data='go_home')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await message.reply_text(
            text=summary,
            parse_mode='HTML',
            reply_markup=reply_markup
        )

    def setup(self):
        self.application.add_handler(CommandHandler('start', self.start_command))
        self.application.add_handler(CommandHandler('analyze', self.analyze_command))
        self.application.add_handler(CommandHandler('credits', self.credits_command))
        self.application.add_handler(CommandHandler('news', self.news_command))
        
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.message_handler))

    def run(self):
        # self.setup_chat_menu()
        self.application.run_polling()
