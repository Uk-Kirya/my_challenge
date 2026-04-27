from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import datetime


class Challenge(Base):
    __tablename__ = "challenges"

    id          = Column(Integer, primary_key=True, index=True)
    title       = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    total_days  = Column(Integer, default=90)
    time_from   = Column(String(5), default="06:00")   # HH:MM
    time_to     = Column(String(5), default="07:00")   # HH:MM
    start_date  = Column(Date, default=datetime.date.today)
    created_at  = Column(DateTime, default=func.now())
    is_active   = Column(Boolean, default=True)

    days = relationship("ChallengeDay", back_populates="challenge",
                        cascade="all, delete-orphan")


class ChallengeDay(Base):
    __tablename__ = "challenge_days"

    id           = Column(Integer, primary_key=True, index=True)
    challenge_id = Column(Integer, ForeignKey("challenges.id"), nullable=False)
    day_number   = Column(Integer, nullable=False)   # 1..N
    date         = Column(Date, nullable=False)
    is_done      = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)

    challenge = relationship("Challenge", back_populates="days")
