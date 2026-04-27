from pydantic import BaseModel
from typing import Optional
import datetime


class ChallengeCreate(BaseModel):
    description: Optional[str] = ""
    total_days: int = 90
    time_from: str = "06:00"
    time_to: str = "07:00"
    start_date: datetime.date = datetime.date.today()


class ChallengeOut(BaseModel):
    id: int
    description: Optional[str]
    total_days: int
    time_from: str
    time_to: str
    start_date: datetime.date
    is_active: bool
    completed_count: int = 0
    streak: int = 0

    class Config:
        from_attributes = True
