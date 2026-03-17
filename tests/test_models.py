"""Model tests for SentimentStream."""

import json
import pytest
from models.schemas import Tweet, Topic, SentimentRecord


def test_tweet_creation(db_session):
    """Tweet ORM model can be created and serialized."""
    tweet = Tweet(
        text="This is a great test tweet! #Python",
        username="@test_user",
        sentiment_score=0.75,
        sentiment_label="positive",
        hashtags=json.dumps(["#Python"]),
        mentions=json.dumps([]),
    )
    db_session.add(tweet)
    db_session.commit()
    db_session.refresh(tweet)

    assert tweet.id is not None
    assert tweet.text == "This is a great test tweet! #Python"
    assert tweet.sentiment_label == "positive"

    d = tweet.to_dict()
    assert d["id"] == tweet.id
    assert d["hashtags"] == ["#Python"]
    assert d["sentiment_score"] == 0.75


def test_topic_creation(db_session):
    """Topic ORM model can be created with keywords."""
    topic = Topic(
        name="Machine Learning",
        keywords=json.dumps(["ai", "ml", "deeplearning"]),
        tweet_count=42,
        avg_sentiment=0.35,
    )
    db_session.add(topic)
    db_session.commit()
    db_session.refresh(topic)

    assert topic.id is not None
    d = topic.to_dict()
    assert d["name"] == "Machine Learning"
    assert "ai" in d["keywords"]
    assert d["tweet_count"] == 42


def test_sentiment_record(db_session):
    """SentimentRecord ORM model stores aggregates correctly."""
    record = SentimentRecord(
        avg_score=0.25,
        positive_count=5,
        negative_count=2,
        neutral_count=3,
        total_count=10,
        dominant_topic="AI",
    )
    db_session.add(record)
    db_session.commit()
    db_session.refresh(record)

    d = record.to_dict()
    assert d["avg_score"] == 0.25
    assert d["total_count"] == 10
    assert d["dominant_topic"] == "AI"
