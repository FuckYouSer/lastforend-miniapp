import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # توکن ربات
    BOT_TOKEN = "8437428190:AAGI__RqJzin1PjbSPCpyz2p5mK_P7-8z2w"
    
    # تنظیمات دیتابیس
    DATABASE_PATH = "data/airdrop.db"
    
    # تنظیمات API
    API_HOST = "0.0.0.0"
    API_PORT = 5000
    
    # تنظیمات توکن
    TOKEN_NAME = "LFE"
    TOKEN_SYMBOL = "LFE"
    TOKEN_DECIMALS = 18
    
    # پاداش‌ها
    REFERRAL_BONUS = 25
    WELCOME_BONUS = 10
    
    # ماموریت‌ها
    TASKS = {
        "join_telegram": {"reward": 50, "name": "Join Telegram Channel"},
        "follow_twitter": {"reward": 30, "name": "Follow Twitter"},
        "invite_friends": {"reward": 25, "name": "Invite Friends"}
    }
    
    # کیف پول‌های پشتیبانی شده
    SUPPORTED_WALLETS = ["Metamask", "Trust Wallet", "Coinbase Wallet", "WalletConnect"]
