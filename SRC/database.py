import sqlite3
import logging
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = "data/airdrop.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """ایجاد اتصال به دیتابیس"""
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """ایجاد جداول دیتابیس"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
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
                    api_key TEXT UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                    FOREIGN KEY (task_id) REFERENCES tasks (id),
                    UNIQUE(user_id, task_id)
                )
            ''')
            
            # جدول دعوت‌ها
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS referrals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    inviter_id INTEGER,
                    invited_id INTEGER,
                    tokens_earned INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (inviter_id) REFERENCES users (id),
                    FOREIGN KEY (invited_id) REFERENCES users (id),
                    UNIQUE(invited_id)
                )
            ''')
            
            # جدول تراکنش‌ها
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    transaction_type TEXT, -- 'task_reward', 'referral_bonus', 'withdrawal'
                    amount INTEGER,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # اضافه کردن ماموریت‌های پیش‌فرض
            self._add_default_tasks(cursor)
            
            conn.commit()
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def _add_default_tasks(self, cursor):
        """اضافه کردن ماموریت‌های پیش‌فرض"""
        default_tasks = [
            ("Join Telegram Channel", "Join our official Telegram channel", 50, "social"),
            ("Follow Twitter", "Follow our Twitter account", 30, "social"),
            ("Retweet Post", "Retweet our latest post", 20, "social"),
            ("Invite 1 Friend", "Invite one friend to join", 25, "referral"),
            ("Invite 5 Friends", "Invite five friends to join", 150, "referral"),
            ("Join Announcement Channel", "Join our announcement channel", 40, "social")
        ]
        
        cursor.executemany('''
            INSERT OR IGNORE INTO tasks (name, description, reward_tokens, task_type)
            VALUES (?, ?, ?, ?)
        ''', default_tasks)
    
    # ===== USER MANAGEMENT =====
    
    def register_user(self, telegram_id: int, username: str, invited_by: int = None) -> Optional[int]:
        """ثبت کاربر جدید"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            referral_code = f"LFE{telegram_id}"
            api_key = f"LFE_API_{telegram_id}_{datetime.now().strftime('%Y%m%d')}"
            
            cursor.execute('''
                INSERT OR IGNORE INTO users 
                (telegram_id, username, referral_code, invited_by, api_key)
                VALUES (?, ?, ?, ?, ?)
            ''', (telegram_id, username, referral_code, invited_by, api_key))
            
            conn.commit()
            
            # اگر کاربر توسط referral آمده باشد
            if invited_by:
                self._handle_referral_bonus(invited_by, telegram_id)
            
            cursor.execute('SELECT id FROM users WHERE telegram_id = ?', (telegram_id,))
            result = cursor.fetchone()
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"Error registering user: {e}")
            return None
        finally:
            conn.close()
    
    def _handle_referral_bonus(self, inviter_id: int, invited_id: int):
        """پرداخت پاداش referral"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # ثبت referral
            cursor.execute('''
                INSERT INTO referrals (inviter_id, invited_id)
                VALUES (?, ?)
            ''', (inviter_id, invited_id))
            
            # اضافه کردن پاداش به inviter
            referral_bonus = 25
            cursor.execute('''
                UPDATE users 
                SET total_tokens = total_tokens + ? 
                WHERE id = ?
            ''', (referral_bonus, inviter_id))
            
            # ثبت تراکنش
            cursor.execute('''
                INSERT INTO transactions (user_id, transaction_type, amount, description)
                VALUES (?, 'referral_bonus', ?, 'Referral bonus for inviting friend')
            ''', (inviter_id, referral_bonus))
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"Error handling referral bonus: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[Dict]:
        """دریافت اطلاعات کاربر"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT u.*, 
                       COUNT(DISTINCT r.invited_id) as referral_count,
                       COUNT(DISTINCT ct.id) as completed_tasks_count
                FROM users u
                LEFT JOIN referrals r ON r.inviter_id = u.id
                LEFT JOIN completed_tasks ct ON ct.user_id = u.id
                WHERE u.telegram_id = ?
                GROUP BY u.id
            ''', (telegram_id,))
            
            result = cursor.fetchone()
            if not result:
                return None
            
            columns = [desc[0] for desc in cursor.description]
            user_data = dict(zip(columns, result))
            
            return user_data
            
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None
        finally:
            conn.close()
    
    def get_user_by_referral_code(self, referral_code: str) -> Optional[Dict]:
        """دریافت کاربر بر اساس کد referral"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT * FROM users WHERE referral_code = ?', (referral_code,))
            result = cursor.fetchone()
            
            if not result:
                return None
            
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, result))
            
        except Exception as e:
            logger.error(f"Error getting user by referral code: {e}")
            return None
        finally:
            conn.close()
    
    # ===== TASK MANAGEMENT =====
    
    def get_available_tasks(self, user_id: int) -> List[Dict]:
        """دریافت ماموریت‌های available برای کاربر"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT t.*, 
                       CASE WHEN ct.id IS NOT NULL THEN 1 ELSE 0 END as completed
                FROM tasks t
                LEFT JOIN completed_tasks ct ON ct.task_id = t.id AND ct.user_id = ?
                WHERE t.is_active = TRUE
                ORDER BY t.created_at
            ''', (user_id,))
            
            results = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            return [dict(zip(columns, row)) for row in results]
            
        except Exception as e:
            logger.error(f"Error getting available tasks: {e}")
            return []
        finally:
            conn.close()
    
    def complete_task(self, user_id: int, task_id: int) -> bool:
        """اتمام ماموریت و پرداخت پاداش"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # بررسی اینکه کاربر قبلاً این ماموریت را انجام داده
            cursor.execute('''
                SELECT 1 FROM completed_tasks 
                WHERE user_id = ? AND task_id = ?
            ''', (user_id, task_id))
            
            if cursor.fetchone():
                return False  # قبلاً انجام شده
            
            # دریافت اطلاعات ماموریت
            cursor.execute('SELECT reward_tokens, name FROM tasks WHERE id = ?', (task_id,))
            task = cursor.fetchone()
            
            if not task:
                return False
            
            reward_tokens, task_name = task
            
            # ثبت ماموریت انجام شده
            cursor.execute('''
                INSERT INTO completed_tasks (user_id, task_id)
                VALUES (?, ?)
            ''', (user_id, task_id))
            
            # اضافه کردن توکن به کاربر
            cursor.execute('''
                UPDATE users 
                SET total_tokens = total_tokens + ? 
                WHERE id = ?
            ''', (reward_tokens, user_id))
            
            # ثبت تراکنش
            cursor.execute('''
                INSERT INTO transactions (user_id, transaction_type, amount, description)
                VALUES (?, 'task_reward', ?, ?)
            ''', (user_id, reward_tokens, f"Task completed: {task_name}"))
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error completing task: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    # ===== WALLET MANAGEMENT =====
    
    def update_wallet_address(self, user_id: int, wallet_address: str) -> bool:
        """بروزرسانی آدرس کیف پول کاربر"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE users 
                SET wallet_address = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (wallet_address, user_id))
            
            conn.commit()
            return cursor.rowcount > 0
            
        except Exception as e:
            logger.error(f"Error updating wallet address: {e}")
            return False
        finally:
            conn.close()
    
    def get_user_transactions(self, user_id: int, limit: int = 10) -> List[Dict]:
        """دریافت تاریخچه تراکنش‌های کاربر"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT transaction_type, amount, description, created_at
                FROM transactions
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            ''', (user_id, limit))
            
            results = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            return [dict(zip(columns, row)) for row in results]
            
        except Exception as e:
            logger.error(f"Error getting transactions: {e}")
            return []
        finally:
            conn.close()
    
    # ===== REFERRAL SYSTEM =====
    
    def get_referral_stats(self, user_id: int) -> Dict:
        """دریافت آمار referral کاربر"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT COUNT(*) as total_referrals,
                       COALESCE(SUM(tokens_earned), 0) as total_earned
                FROM referrals
                WHERE inviter_id = ?
            ''', (user_id,))
            
            result = cursor.fetchone()
            
            return {
                'total_referrals': result[0] if result else 0,
                'total_earned': result[1] if result else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting referral stats: {e}")
            return {'total_referrals': 0, 'total_earned': 0}
        finally:
            conn.close()
    
    def get_referral_leaderboard(self, limit: int = 10) -> List[Dict]:
        """دریافت لیدربرد referrals"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT u.username, u.telegram_id,
                       COUNT(r.invited_id) as referral_count,
                       u.total_tokens
                FROM users u
                LEFT JOIN referrals r ON r.inviter_id = u.id
                GROUP BY u.id
                ORDER BY referral_count DESC, u.total_tokens DESC
                LIMIT ?
            ''', (limit,))
            
            results = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            return [dict(zip(columns, row)) for row in results]
            
        except Exception as e:
            logger.error(f"Error getting referral leaderboard: {e}")
            return []
        finally:
            conn.close()

# نمونه global برای استفاده در سایر فایل‌ها
db = DatabaseManager()
