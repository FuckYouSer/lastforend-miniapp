"""
LastForEnd Telegram Bot - Advanced Airdrop Platform
"""

__version__ = "1.0.0"
__author__ = "LastForEnd Team"
__description__ = "Advanced Telegram Airdrop Bot with API, Referral & Wallet System"

# Import main components for easier access
from .database import DatabaseManager, db
from .bot import LastForEndBot

# Export main classes and functions
__all__ = [
    'DatabaseManager',
    'db',
    'LastForEndBot',
    'run_bot'
]

# Configuration
BOT_CONFIG = {
    "name": "LastForEnd Airdrop Bot",
    "version": "1.0.0",
    "token": "8437428190:AAGI__RqJzin1PjbSPCpyz2p5mK_P7-8z2w",
    "database_path": "data/airdrop.db",
    "supported_wallets": ["Metamask", "Trust Wallet", "Coinbase Wallet"],
    "default_tasks": [
        {
            "name": "Join Telegram Channel",
            "reward": 50,
            "type": "social"
        },
        {
            "name": "Invite Friends", 
            "reward": 25,
            "type": "referral"
        }
    ]
}

def get_version():
    """Return the current version of the bot"""
    return __version__

def get_bot_info():
    """Return bot information"""
    return {
        "name": BOT_CONFIG["name"],
        "version": __version__,
        "description": __description__,
        "author": __author__
    }

def run_bot(token: str = None):
    """
    Start the LastForEnd bot
    
    Args:
        token (str): Telegram bot token. If None, uses default token.
    
    Returns:
        LastForEndBot: The bot instance
    """
    bot_token = token or BOT_CONFIG["token"]
    bot = LastForEndBot(bot_token)
    
    print(f"🚀 Starting {BOT_CONFIG['name']} v{__version__}")
    print(f"📝 {__description__}")
    print("🔗 Database initialized at:", BOT_CONFIG["database_path"])
    
    try:
        bot.run()
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
    
    return bot

def init_database():
    """
    Initialize database tables
    """
    db.init_database()
    print("✅ Database initialized successfully")

# Auto-initialize database when module is imported
try:
    init_database()
except Exception as e:
    print(f"⚠️  Database initialization warning: {e}")

if __name__ == "__main__":
    # If this file is run directly, start the bot
    run_bot()
