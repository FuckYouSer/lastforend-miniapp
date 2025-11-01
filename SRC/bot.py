import logging
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ایمپورت دیتابیس
from src.database import db

# تنظیمات لاگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

class LastForEndBot:
    def __init__(self, token: str):
        self.token = token
        self.app = Application.builder().token(token).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        """تنظیم هندلرهای ربات"""
        # دستورات اصلی
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("wallet", self.wallet_command))
        self.app.add_handler(CommandHandler("tasks", self.tasks_command))
        self.app.add_handler(CommandHandler("invite", self.invite_command))
        self.app.add_handler(CommandHandler("profile", self.profile_command))
        self.app.add_handler(CommandHandler("leaderboard", self.leaderboard_command))
        
        # هندلرهای اینلاین
        self.app.add_handler(CallbackQueryHandler(self.button_handler))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """دستور شروع ربات"""
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        # بررسی referral code از آرگومان
        referral_code = None
        if context.args and len(context.args) > 0:
            referral_code = context.args[0]
        
        # ثبت کاربر در دیتابیس
        invited_by = None
        if referral_code:
            referrer = db.get_user_by_referral_code(referral_code)
            if referrer:
                invited_by = referrer['id']
        
        user_id = db.register_user(user.id, user.username, invited_by)
        
        # ایجاد منوی اصلی
        keyboard = [
            [InlineKeyboardButton("💰 START EARNING", callback_data="earn")],
            [InlineKeyboardButton("📊 MY WALLET", callback_data="wallet")],
            [InlineKeyboardButton("👥 INVITE FRIENDS", callback_data="invite")],
            [InlineKeyboardButton("📋 AVAILABLE TASKS", callback_data="tasks")],
            [InlineKeyboardButton("👤 MY PROFILE", callback_data="profile")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = f"""
🚀 **Welcome to LastForEnd, {user.first_name}!**

Your final opportunity for financial freedom begins here.

🔹 **Earn LFE tokens effortlessly**
🔹 **Invite friends for bonus rewards**  
🔹 **Connect your wallet securely**

Start your journey to financial independence today!
        """
        
        if referral_code and invited_by:
            welcome_text += f"\n\n🎉 You were invited by a friend! +25 LFE bonus!"
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def wallet_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش کیف پول کاربر"""
        user = update.effective_user
        user_data = db.get_user_by_telegram_id(user.id)
        
        if not user_data:
            await update.message.reply_text("❌ User not found. Please use /start first.")
            return
        
        wallet_text = f"""
💼 **Your LastForEnd Wallet**

💰 **Balance:** `{user_data['total_tokens']} LFE`
🌐 **Network:** Ethereum ERC-20

"""
        
        if user_data['wallet_address']:
            wallet_text += f"🔗 **Connected Wallet:** `{user_data['wallet_address'][:10]}...{user_data['wallet_address'][-8:]}`"
        else:
            wallet_text += "🔗 **Wallet Status:** Not connected"
        
        keyboard = [
            [InlineKeyboardButton("🔗 Connect Wallet", callback_data="connect_wallet")],
            [InlineKeyboardButton("💳 Withdraw Tokens", callback_data="withdraw")],
            [InlineKeyboardButton("📊 Transaction History", callback_data="transactions")],
            [InlineKeyboardButton("🔄 Refresh", callback_data="refresh_wallet")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(wallet_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def tasks_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش ماموریت‌های available"""
        user = update.effective_user
        user_data = db.get_user_by_telegram_id(user.id)
        
        if not user_data:
            await update.message.reply_text("❌ User not found. Please use /start first.")
            return
        
        tasks = db.get_available_tasks(user_data['id'])
        
        if not tasks:
            await update.message.reply_text("📭 No tasks available at the moment.")
            return
        
        tasks_text = "📋 **Available Tasks**\n\n"
        
        for task in tasks:
            status = "✅" if task['completed'] else "⭕"
            tasks_text += f"{status} **{task['name']}**\n"
            tasks_text += f"📝 {task['description']}\n"
            tasks_text += f"💰 Reward: `{task['reward_tokens']} LFE`\n"
            
            if not task['completed']:
                tasks_text += f"🆔 Complete with: `/complete_{task['id']}`\n"
            
            tasks_text += "\n"
        
        keyboard = [
            [InlineKeyboardButton("🔄 Refresh Tasks", callback_data="refresh_tasks")],
            [InlineKeyboardButton("📊 My Progress", callback_data="task_progress")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(tasks_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def invite_command(self, Update: Update, context: ContextTypes.DEFAULT_TYPE):
        """سیستم دعوت دوستان"""
        user = update.effective_user
        user_data = db.get_user_by_telegram_id(user.id)
        
        if not user_data:
            await update.message.reply_text("❌ User not found. Please use /start first.")
            return
        
        referral_stats = db.get_referral_stats(user_data['id'])
        referral_code = user_data['referral_code']
        
        invite_text = f"""
👥 **Invite Friends & Earn**

Invite your friends to join LastForEnd and earn bonus tokens!

🔗 **Your Referral Link:**
`https://t.me/LastForEndBot?start={referral_code}`

📊 **Your Referral Stats:**
👥 Total Referrals: `{referral_stats['total_referrals']}`
💰 Total Earned: `{referral_stats['total_earned']} LFE`

🎁 **Rewards:**
• 25 LFE for each successful referral
• 10% of your friend's earnings
        """
        
        keyboard = [
            [InlineKeyboardButton("📤 Share Link", callback_data="share_link")],
            [InlineKeyboardButton("📊 Referral Stats", callback_data="referral_stats")],
            [InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(invite_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def profile_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پروفایل کاربر"""
        user = update.effective_user
        user_data = db.get_user_by_telegram_id(user.id)
        
        if not user_data:
            await update.message.reply_text("❌ User not found. Please use /start first.")
            return
        
        referral_stats = db.get_referral_stats(user_data['id'])
        
        profile_text = f"""
👤 **Your Profile**

🆔 **User ID:** `{user.id}`
📛 **Username:** @{user.username if user.username else 'N/A'}
💰 **Total Balance:** `{user_data['total_tokens']} LFE`
👥 **Referrals:** `{referral_stats['total_referrals']}`
📊 **Tasks Completed:** `{user_data['completed_tasks_count']}`
📅 **Member Since:** `{user_data['created_at'][:10]}`

🌐 **API Key:** `{user_data['api_key']}`
🔗 **Referral Code:** `{user_data['referral_code']}`
        """
        
        keyboard = [
            [InlineKeyboardButton("🔄 Refresh", callback_data="refresh_profile")],
            [InlineKeyboardButton("📊 Transactions", callback_data="transactions")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(profile_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def leaderboard_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """لیدربرد بهترین referralها"""
        leaderboard = db.get_referral_leaderboard(10)
        
        if not leaderboard:
            await update.message.reply_text("📊 No leaderboard data available yet.")
            return
        
        leaderboard_text = "🏆 **Referral Leaderboard**\n\n"
        
        for i, user in enumerate(leaderboard, 1):
            username = user['username'] or f"User{user['telegram_id']}"
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            
            leaderboard_text += f"{medal} **{username}**\n"
            leaderboard_text += f"   👥 Referrals: `{user['referral_count']}` | 💰 Balance: `{user['total_tokens']} LFE`\n\n"
        
        await update.message.reply_text(leaderboard_text, parse_mode='Markdown')
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """مدیریت کلیک روی دکمه‌ها"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "earn":
            await self.tasks_command(update, context)
        elif data == "wallet":
            await self.wallet_command(update, context)
        elif data == "invite":
            await self.invite_command(update, context)
        elif data == "tasks":
            await self.tasks_command(update, context)
        elif data == "profile":
            await self.profile_command(update, context)
        elif data == "leaderboard":
            await self.leaderboard_command(update, context)
        elif data == "refresh_tasks":
            await query.edit_message_text("🔄 Refreshing tasks...")
            await self.tasks_command(update, context)
        elif data == "refresh_wallet":
            await query.edit_message_text("🔄 Refreshing wallet...")
            await self.wallet_command(update, context)
        elif data == "refresh_profile":
            await query.edit_message_text("🔄 Refreshing profile...")
            await self.profile_command(update, context)
        elif data == "connect_wallet":
            await query.edit_message_text(
                "🔗 **Wallet Connection**\n\n"
                "Please use our Mini App to connect your external wallet securely.\n\n"
                "Or send your wallet address in this format:\n"
                "`/connect_wallet 0xYourWalletAddress`"
            )
        elif data == "transactions":
            await self.show_transactions(update, context)
        elif data == "share_link":
            user_data = db.get_user_by_telegram_id(query.from_user.id)
            if user_data:
                referral_link = f"https://t.me/LastForEndBot?start={user_data['referral_code']}"
                await query.edit_message_text(
                    f"📤 **Share this link with your friends:**\n\n"
                    f"`{referral_link}`\n\n"
                    f"Each friend who joins through this link earns you 25 LFE!"
                )
    
    async def show_transactions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش تراکنش‌های کاربر"""
        query = update.callback_query
        user = query.from_user
        user_data = db.get_user_by_telegram_id(user.id)
        
        if not user_data:
            await query.edit_message_text("❌ User not found.")
            return
        
        transactions = db.get_user_transactions(user_data['id'], 10)
        
        if not transactions:
            await query.edit_message_text("📭 No transactions found.")
            return
        
        transactions_text = "📊 **Recent Transactions**\n\n"
        
        for tx in transactions:
            emoji = "🟢" if tx['amount'] > 0 else "🔴"
            date = tx['created_at'][:16]
            transactions_text += f"{emoji} **{tx['transaction_type'].replace('_', ' ').title()}**\n"
            transactions_text += f"   Amount: `{tx['amount']} LFE`\n"
            transactions_text += f"   Date: `{date}`\n"
            transactions_text += f"   Desc: {tx['description']}\n\n"
        
        await query.edit_message_text(transactions_text, parse_mode='Markdown')
    
    def run(self):
        """اجرای ربات"""
        print("🚀 LastForEnd Bot is running...")
        self.app.run_polling()

# اجرای ربات
if __name__ == '__main__':
    BOT_TOKEN = "8437428190:AAGI__RqJzin1PjbSPCpyz2p5mK_P7-8z2w"
    
    bot = LastForEndBot(BOT_TOKEN)
    bot.run()
