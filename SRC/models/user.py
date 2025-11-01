from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class User:
    id: Optional[int]
    telegram_id: int
    username: Optional[str]
    referral_code: str
    invited_by: Optional[int]
    wallet_address: Optional[str]
    total_tokens: int
    is_verified: bool
    api_key: str
    created_at: datetime
    updated_at: datetime
    
    def to_dict(self):
        return {
            "id": self.id,
            "telegram_id": self.telegram_id,
            "username": self.username,
            "referral_code": self.referral_code,
            "wallet_address": self.wallet_address,
            "total_tokens": self.total_tokens,
            "api_key": self.api_key
        }
