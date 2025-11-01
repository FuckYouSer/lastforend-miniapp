from .database import db
from .config import Config
import logging

logger = logging.getLogger(__name__)

class TaskManager:
    def __init__(self):
        self.tasks = Config.TASKS
    
    def get_available_tasks_for_user(self, telegram_id: int) -> list:
        """دریافت ماموریت‌های available برای کاربر"""
        user = db.get_user_by_telegram_id(telegram_id)
        if not user:
            return []
        
        return db.get_available_tasks(user['id'])
    
    def complete_social_task(self, telegram_id: int, task_type: str) -> bool:
        """اتمام ماموریت اجتماعی"""
        user = db.get_user_by_telegram_id(telegram_id)
        if not user:
            return False
        
        # پیدا کردن task_id بر اساس نوع
        # اینجا نیاز به منطق خاص داری
        return True
    
    def check_channel_membership(self, telegram_id: int, channel_username: str) -> bool:
        """بررسی عضویت در کانال (شبیه‌سازی)"""
        # در حالت واقعی از Telegram API استفاده میشه
        return True
    
    def verify_twitter_follow(self, telegram_id: int, twitter_username: str) -> bool:
        """بررسی فالو توئیتر (شبیه‌سازی)"""
        # در حالت واقعی از Twitter API استفاده میشه
        return True

# نمونه global
task_manager = TaskManager()
