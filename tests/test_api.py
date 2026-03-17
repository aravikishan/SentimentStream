"""API endpoint tests for SentimentStream."""

import pytest


def test_health_check(client):
    """Health endpoint returns healthy status."""
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["service"] == "SentimentStream"


def test_list_tweets_empty(client):
    """Listing tweets on empty database returns empty list."""
    resp = client.get("/api/tweets")
    assert resp.status_code == 200
    data = resp.json()
    assert data["tweets"] == []
    assert data["total"] == 0


def test_stream_tweets(client):
    """Stream endpoint generates and returns tweets."""
    resp = client.get("/api/tweets/stream?count=3")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 3
    assert len(data["tweets"]) == 3
    for tweet in data["tweets"]:
        assert "text" in tweet
        assert "sentiment_label" in tweet
        assert tweet["sentiment_label"] in ("positive", "negative", "neutral")


def test_generate_tweets(client):
    """Generate endpoint creates specified number of tweets."""
    resp = client.post("/api/tweets/generate?count=5")
    assert resp.status_code == 200
    data = resp.json()
    assert data["generated"] == 5
    assert len(data["tweets"]) == 5


def test_analyze_text(client):
    """Analyze endpoint correctly classifies positive text."""
    resp = client.post(
        "/api/analyze",
        json={"text": "This is absolutely amazing and wonderful!"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["label"] == "positive"
    assert data["score"] > 0
    assert data["word_count"] > 0


def test_analyze_negative_text(client):
    """Analyze endpoint correctly classifies negative text."""
    resp = client.post(
        "/api/analyze",
        json={"text": "This is terrible and awful, I hate it."},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["label"] == "negative"
    assert data["score"] < 0


def test_sentiment_stats(client):
    """Stats endpoint returns correct aggregate stats."""
    # Generate some tweets first
    client.post("/api/tweets/generate?count=10")
    resp = client.get("/api/sentiment/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_tweets"] == 10
    assert data["positive_count"] + data["negative_count"] + data["neutral_count"] == 10


def test_topics_empty(client):
    """Topics endpoint returns empty list on fresh database."""
    resp = client.get("/api/topics")
    assert resp.status_code == 200
    data = resp.json()
    assert data["topics"] == []


def test_topic_not_found(client):
    """Topic detail endpoint returns 404 for missing topic."""
    resp = client.get("/api/topics/9999")
    assert resp.status_code == 404


def test_trends_endpoint(client):
    """Trends endpoint returns valid structure."""
    resp = client.get("/api/trends")
    assert resp.status_code == 200
    data = resp.json()
    assert "sentiment_history" in data
    assert "top_topics" in data
    assert "alerts" in data
