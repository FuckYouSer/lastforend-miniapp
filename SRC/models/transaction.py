from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum

class TransactionType(Enum):
    TASK_REWARD = "task_reward"
    REFERRAL_BONUS = "referral_bonus"
    WELCOME_BONUS = "welcome_bonus"
    WITHDRAWAL = "withdrawal"
    AIRDROP = "airdrop"
    MANUAL_ADJUSTMENT = "manual_adjustment"

class TransactionStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class Transaction:
    id: Optional[int]
    user_id: int
    transaction_type: TransactionType
    amount: int
    description: str
    status: TransactionStatus
    created_at: datetime
    
    # فیلدهای اختیاری
    related_task_id: Optional[int] = None
    related_referral_id: Optional[int] = None
    wallet_address: Optional[str] = None
    transaction_hash: Optional[str] = None
    metadata: Optional[dict] = None
    
    def to_dict(self):
        """تبدیل به دیکشنری"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "transaction_type": self.transaction_type.value,
            "amount": self.amount,
            "description": self.description,
            "status": self.status.value,
            "related_task_id": self.related_task_id,
            "related_referral_id": self.related_referral_id,
            "wallet_address": self.wallet_address,
            "transaction_hash": self.transaction_hash,
            "metadata": self.metadata or {},
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
    
    def is_positive(self) -> bool:
        """بررسی مثبت بودن تراکنش"""
        return self.amount > 0
    
    def get_emoji(self) -> str:
        """دریافت ایموجی مناسب برای نوع تراکنش"""
        emoji_map = {
            TransactionType.TASK_REWARD: "✅",
            TransactionType.REFERRAL_BONUS: "👥",
            TransactionType.WELCOME_BONUS: "🎁",
            TransactionType.WITHDRAWAL: "💳",
            TransactionType.AIRDROP: "🎯",
            TransactionType.MANUAL_ADJUSTMENT: "⚙️"
        }
        return emoji_map.get(self.transaction_type, "📊")
    
    def get_status_color(self) -> str:
        """دریافت رنگ وضعیت"""
        color_map = {
            TransactionStatus.PENDING: "🟡",
            TransactionStatus.COMPLETED: "🟢",
            TransactionStatus.FAILED: "🔴",
            TransactionStatus.CANCELLED: "⚫"
        }
        return color_map.get(self.status, "⚪")
    
    @classmethod
    def create_task_reward(cls, user_id: int, amount: int, task_name: str, task_id: int = None):
        """ایجاد تراکنش پاداش ماموریت"""
        return cls(
            id=None,
            user_id=user_id,
            transaction_type=TransactionType.TASK_REWARD,
            amount=amount,
            description=f"Task reward: {task_name}",
            status=TransactionStatus.COMPLETED,
            related_task_id=task_id,
            created_at=datetime.now()
        )
    
    @classmethod
    def create_referral_bonus(cls, user_id: int, amount: int, referral_id: int = None):
        """ایجاد تراکنش پاداش referral"""
        return cls(
            id=None,
            user_id=user_id,
            transaction_type=TransactionType.REFERRAL_BONUS,
            amount=amount,
            description="Referral bonus",
            status=TransactionStatus.COMPLETED,
            related_referral_id=referral_id,
            created_at=datetime.now()
        )
    
    @classmethod
    def create_withdrawal(cls, user_id: int, amount: int, wallet_address: str):
        """ایجاد تراکنش برداشت"""
        return cls(
            id=None,
            user_id=user_id,
            transaction_type=TransactionType.WITHDRAWAL,
            amount=-amount,  # منفی برای برداشت
            description=f"Withdrawal to {wallet_address[:8]}...",
            status=TransactionStatus.PENDING,
            wallet_address=wallet_address,
            created_at=datetime.now()
        )
    
    def mark_completed(self, transaction_hash: str = None):
        """علامت گذاری به عنوان completed"""
        self.status = TransactionStatus.COMPLETED
        if transaction_hash:
            self.transaction_hash = transaction_hash
    
    def mark_failed(self):
        """علامت گذاری به عنوان failed"""
        self.status = TransactionStatus.FAILED
