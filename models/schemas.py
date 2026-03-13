"""SQLAlchemy ORM models and Pydantic schemas for SentimentStream."""

import json
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from models.database import Base


# ---------------------------------------------------------------------------
# SQLAlchemy ORM Models
# ---------------------------------------------------------------------------

class Tweet(Base):
    """A single tweet (simulated) with sentiment analysis results."""

    __tablename__ = "tweets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(Text, nullable=False)
    username = Column(String(64), nullable=False, default="@user")
    sentiment_score = Column(Float, nullable=False, default=0.0)
    sentiment_label = Column(String(16), nullable=False, default="neutral")
    hashtags = Column(Text, default="[]")
    mentions = Column(Text, default="[]")
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=True)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    topic = relationship("Topic", back_populates="tweets")

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "text": self.text,
            "username": self.username,
            "sentiment_score": round(self.sentiment_score, 3),
            "sentiment_label": self.sentiment_label,
            "hashtags": json.loads(self.hashtags) if self.hashtags else [],
            "mentions": json.loads(self.mentions) if self.mentions else [],
            "topic_id": self.topic_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Topic(Base):
    """A topic cluster derived from tweet analysis."""

    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False, unique=True)
    keywords = Column(Text, default="[]")
    tweet_count = Column(Integer, default=0)
    avg_sentiment = Column(Float, default=0.0)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    tweets = relationship("Tweet", back_populates="topic", lazy="dynamic")

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "keywords": json.loads(self.keywords) if self.keywords else [],
            "tweet_count": self.tweet_count,
            "avg_sentiment": round(self.avg_sentiment, 3),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class SentimentRecord(Base):
    """Time-series record of aggregate sentiment measurements."""

    __tablename__ = "sentiment_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    avg_score = Column(Float, nullable=False, default=0.0)
    positive_count = Column(Integer, default=0)
    negative_count = Column(Integer, default=0)
    neutral_count = Column(Integer, default=0)
    total_count = Column(Integer, default=0)
    dominant_topic = Column(String(128), nullable=True)

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "avg_score": round(self.avg_score, 3),
            "positive_count": self.positive_count,
            "negative_count": self.negative_count,
            "neutral_count": self.neutral_count,
            "total_count": self.total_count,
            "dominant_topic": self.dominant_topic,
        }


# ---------------------------------------------------------------------------
# Pydantic Schemas (request / response)
# ---------------------------------------------------------------------------

class TweetResponse(BaseModel):
    """Response schema for a single tweet."""
    id: int
    text: str
    username: str
    sentiment_score: float
    sentiment_label: str
    hashtags: list[str] = Field(default_factory=list)
    mentions: list[str] = Field(default_factory=list)
    topic_id: Optional[int] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class TopicResponse(BaseModel):
    """Response schema for a topic cluster."""
    id: int
    name: str
    keywords: list[str] = Field(default_factory=list)
    tweet_count: int = 0
    avg_sentiment: float = 0.0
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class AnalyzeRequest(BaseModel):
    """Request body for custom text analysis."""
    text: str = Field(..., min_length=1, max_length=5000)


class AnalyzeResponse(BaseModel):
    """Response for sentiment analysis of custom text."""
    text: str
    score: float
    label: str
    positive_words: list[str] = Field(default_factory=list)
    negative_words: list[str] = Field(default_factory=list)
    word_count: int = 0


class SentimentStatsResponse(BaseModel):
    """Aggregate sentiment statistics."""
    total_tweets: int = 0
    positive_count: int = 0
    negative_count: int = 0
    neutral_count: int = 0
    avg_score: float = 0.0
    positive_pct: float = 0.0
    negative_pct: float = 0.0
    neutral_pct: float = 0.0


class TrendAlert(BaseModel):
    """A single trend alert."""
    alert_type: str
    message: str
    severity: str = "info"
    topic: Optional[str] = None
    value: Optional[float] = None


class TrendResponse(BaseModel):
    """Trend data response."""
    sentiment_history: list[dict] = Field(default_factory=list)
    volume_history: list[dict] = Field(default_factory=list)
    top_topics: list[dict] = Field(default_factory=list)
    alerts: list[TrendAlert] = Field(default_factory=list)
