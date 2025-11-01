import logging
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

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
        self.init_database()
    
    def init_database(self):
        """ایجاد دیتابیس و جداول"""
        conn = sqlite3.connect('data/airdrop.db')
        cursor = conn.cursor()
        
        # جدول کاربران
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE,
                username TEXT,
                referral_code TEXT UNIQUE,
                invited_by INTEGER,
                wallet_address TEXT,
                total_tokens INTEGER DEFAULT 0,
                is_verified BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول ماموریت‌ها
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                description TEXT,
                reward_tokens INTEGER,
                task_type TEXT,
                is_active BOOLEAN DEFAULT TRUE
            )
        ''')
        
        # جدول ماموریت‌های انجام شده
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS completed_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                task_id INTEGER,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (task_id) REFERENCES tasks (id)
            )
        ''')
        
        # اضافه کردن ماموریت‌های پیش‌فرض
        default_tasks = [
            ("Join Telegram Channel", "Join our official channel", 50, "social"),
            ("Invite Friends", "Invite friends to join", 25, "referral"),
            ("Follow Twitter", "Follow our Twitter account", 30, "social"),
            ("Retweet Post", "Retweet our latest post", 20, "social")
        ]
        
        cursor.executemany('''
            INSERT OR IGNORE INTO tasks (name, description, reward_tokens, task_type)
            VALUES (?, ?, ?, ?)
        ''', default_tasks)
        
        conn.commit()
        conn.close()
    
    def setup_handlers(self):
        """تنظیم هندلرهای ربات"""
        # دستورات اصلی
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("wallet", self.wallet_command))
        self.app.add_handler(CommandHandler("tasks", self.tasks_command))
        self.app.add_handler(CommandHandler("invite", self.invite_command))
        self.app.add_handler(CommandHandler("profile", self.profile_command))
        
        # هندلرهای اینلاین
        self.app.add_handler(CallbackQueryHandler(self.button_handler))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """دستور شروع ربات"""
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        # ثبت کاربر در دیتابیس
        user_id = self.register_user(user.id, user.username)
        
        # ایجاد منوی اصلی
        keyboard = [
            [InlineKeyboardButton("💰 START EARNING", callback_data="earn")],
            [InlineKeyboardButton("📊 MY WALLET", callback_data="wallet")],
            [InlineKeyboardButton("👥 INVITE FRIENDS", callback_data="invite")],
            [InlineKeyboardButton("📋 AVAILABLE TASKS", callback_data="tasks")]
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
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    def register_user(self, telegram_id: int, username: str) -> int:
        """ثبت کاربر جدید در دیتابیس"""
        conn = sqlite3.connect('data/airdrop.db')
        cursor = conn.cursor()
        
        # تولید کد referral
        referral_code = f"LFE{telegram_id}{hash(username) % 10000 if username else 0}"
        
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO users (telegram_id, username, referral_code)
                VALUES (?, ?, ?)
            ''', (telegram_id, username, referral_code))
            
            conn.commit()
            
            # گرفتن ID کاربر
            cursor.execute('SELECT id FROM users WHERE telegram_id = ?', (telegram_id,))
            user_id = cursor.fetchone()[0]
            
            return user_id
            
        except Exception as e:
            logging.error(f"Error registering user: {e}")
            return None
        finally:
            conn.close()
    
    async def wallet_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش کیف پول کاربر"""
        user = update.effective_user
        balance = self.get_user_balance(user.id)
        
        wallet_text = f"""
💼 **Your LastForEnd Wallet**

💰 **Balance:** `{balance} LFE`
🌐 **Network:** Ethereum ERC-20

🔗 **Connect your external wallet to withdraw tokens**
        """
        
        keyboard = [
            [InlineKeyboardButton("🔗 Connect Wallet", callback_data="connect_wallet")],
            [InlineKeyboardButton("💳 Withdraw Tokens", callback_data="withdraw")],
            [InlineKeyboardButton("📊 Transaction History", callback_data="transactions")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(wallet_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    def get_user_balance(self, telegram_id: int) -> int:
        """دریافت موجودی کاربر"""
        conn = sqlite3.connect('data/airdrop.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT total_tokens FROM users WHERE telegram_id = ?', (telegram_id,))
        result = cursor.fetchone()
        
        conn.close()
        
        return result[0] if result else 0
    
    async def tasks_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش ماموریت‌های available"""
        tasks = self.get_available_tasks()
        
        tasks_text = "📋 **Available Tasks**\n\n"
        for task in tasks:
            tasks_text += f"🎯 **{task[1]}**\n"
            tasks_text += f"📝 {task[2]}\n"
            tasks_text += f"💰 Reward: `{task[3]} LFE`\n\n"
        
        keyboard = [[InlineKeyboardButton("🔄 Refresh Tasks", callback_data="refresh_tasks")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(tasks_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    def get_available_tasks(self):
        """دریافت ماموریت‌های فعال"""
        conn = sqlite3.connect('data/airdrop.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM tasks WHERE is_active = TRUE')
        tasks = cursor.fetchall()
        
        conn.close()
        return tasks
    
    async def invite_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """سیستم دعوت دوستان"""
        user = update.effective_user
        referral_code = self.get_referral_code(user.id)
        
        invite_text = f"""
👥 **Invite Friends & Earn**

Invite your friends to join LastForEnd and earn bonus tokens!

🔗 **Your Referral Link:**
`https://t.me/LastForEndBot?start={referral_code}`

📊 **Your Referral Stats:**
👥 Referrals: `{self.get_referral_count(user.id)}`
💰 Total Earned: `{self.get_referral_earnings(user.id)} LFE`

🎁 **Rewards:**
• 25 LFE for each successful referral
• 10% of your friend's earnings
        """
        
        keyboard = [
            [InlineKeyboardButton("📤 Share Link", callback_data="share_link")],
            [InlineKeyboardButton("📊 Referral Stats", callback_data="referral_stats")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(invite_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    def get_referral_code(self, telegram_id: int) -> str:
        """دریافت کد referral کاربر"""
        conn = sqlite3.connect('data/airdrop.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT referral_code FROM users WHERE telegram_id = ?', (telegram_id,))
        result = cursor.fetchone()
        
        conn.close()
        return result[0] if result else ""
    
    async def profile_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پروفایل کاربر"""
        user = update.effective_user
        user_data = self.get_user_data(user.id)
        
        profile_text = f"""
👤 **Your Profile**

🆔 **User ID:** `{user.id}`
📛 **Username:** @{user.username if user.username else 'N/A'}
💰 **Total Balance:** `{user_data['balance']} LFE`
👥 **Referrals:** `{user_data['referrals']}`
📊 **Tasks Completed:** `{user_data['completed_tasks']}`

🌐 **API Key:** `{user_data['api_key']}`
        """
        
        await update.message.reply_text(profile_text, parse_mode='Markdown')
    
    def get_user_data(self, telegram_id: int) -> dict:
        """دریافت اطلاعات کاربر"""
        conn = sqlite3.connect('data/airdrop.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT u.total_tokens, u.referral_code,
                   COUNT(DISTINCT r.id) as referral_count,
                   COUNT(DISTINCT ct.id) as completed_tasks
            FROM users u
            LEFT JOIN users r ON r.invited_by = u.id
            LEFT JOIN completed_tasks ct ON ct.user_id = u.id
            WHERE u.telegram_id = ?
            GROUP BY u.id
        ''', (telegram_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'balance': result[0],
                'api_key': f"LFE_API_{telegram_id}",
                'referrals': result[2],
                'completed_tasks': result[3]
            }
        return {'balance': 0, 'api_key': 'N/A', 'referrals': 0, 'completed_tasks': 0}
    
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
        elif data == "connect_wallet":
            await query.edit_message_text("🔗 **Wallet Connection**\n\nPlease use our Mini App to connect your external wallet securely.")
    
    def run(self):
        """اجرای ربات"""
        print("🚀 LastForEnd Bot is running...")
        self.app.run_polling()

# اجرای ربات
if __name__ == '__main__':
    # توکن ربات رو اینجا قرار بده
    BOT_TOKEN = "8437428190:AAGI__RqJzin1PjbSPCpyz2p5mK_P7-8z2w"
    
    bot = LastForEndBot(8437428190:AAGI__RqJzin1PjbSPCpyz2p5mK_P7-8z2w)
    bot.run()
