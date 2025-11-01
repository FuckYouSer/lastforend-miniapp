from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Task:
    id: Optional[int]
    name: str
    description: str
    reward_tokens: int
    task_type: str  # 'social', 'referral', 'content', 'verification'
    is_active: bool
    created_at: datetime
    
    # تنظیمات خاص هر نوع ماموریت
    social_platform: Optional[str] = None  # 'telegram', 'twitter', 'discord'
    verification_url: Optional[str] = None
    max_completions: Optional[int] = None  # حداکثر تعداد تکرار
    cooldown_hours: Optional[int] = None   # زمان انتظار بین تکرار
    
    def to_dict(self):
        """تبدیل به دیکشنری"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "reward_tokens": self.reward_tokens,
            "task_type": self.task_type,
            "is_active": self.is_active,
            "social_platform": self.social_platform,
            "verification_url": self.verification_url,
            "max_completions": self.max_completions,
            "cooldown_hours": self.cooldown_hours,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
    
    def is_available_for_user(self, user_completed_count: int = 0) -> bool:
        """بررسی availability ماموریت برای کاربر"""
        if not self.is_active:
            return False
        
        if self.max_completions and user_completed_count >= self.max_completions:
            return False
            
        return True
    
    def get_task_instructions(self) -> str:
        """دریافت دستورالعمل انجام ماموریت"""
        instructions = {
            "social": f"Join our {self.social_platform} channel and stay member",
            "referral": "Invite friends using your referral link",
            "content": "Create and share content about LastForEnd",
            "verification": f"Verify your account by visiting: {self.verification_url}"
        }
        
        return instructions.get(self.task_type, "Complete the task to earn rewards")
    
    @classmethod
    def create_social_task(cls, name: str, platform: str, reward: int, description: str = None):
        """ایجاد ماموریت اجتماعی"""
        if not description:
            description = f"Join our {platform} community"
            
        return cls(
            id=None,
            name=name,
            description=description,
            reward_tokens=reward,
            task_type="social",
            social_platform=platform,
            is_active=True,
            created_at=datetime.now()
        )
    
    @classmethod
    def create_referral_task(cls, name: str, reward: int, max_completions: int = None):
        """ایجاد ماموریت referral"""
        return cls(
            id=None,
            name=name,
            description="Invite friends to join LastForEnd",
            reward_tokens=reward,
            task_type="referral",
            max_completions=max_completions,
            is_active=True,
            created_at=datetime.now()
        )
