"""REST API endpoints for SentimentStream."""

import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from models.database import get_db
from models.schemas import (
    Tweet, Topic, SentimentRecord,
    AnalyzeRequest, AnalyzeResponse,
    SentimentStatsResponse, TrendResponse, TrendAlert,
)
from services.sentiment import SentimentAnalyzer
from services.stream import TweetStreamSimulator, TopicClusterer, TrendDetector

router = APIRouter(prefix="/api", tags=["api"])
analyzer = SentimentAnalyzer()


@router.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "SentimentStream"}


# ---------------------------------------------------------------------------
# Tweet endpoints
# ---------------------------------------------------------------------------

@router.get("/tweets")
def list_tweets(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    label: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """List recent tweets with optional sentiment label filter."""
    query = db.query(Tweet).order_by(desc(Tweet.created_at))
    if label and label in ("positive", "negative", "neutral"):
        query = query.filter(Tweet.sentiment_label == label)
    tweets = query.offset(offset).limit(limit).all()
    total = query.count()
    return {
        "tweets": [t.to_dict() for t in tweets],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/tweets/stream")
def stream_tweets(
    count: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
):
    """Get the latest batch of tweets from the simulated stream."""
    simulator = TweetStreamSimulator()
    batch = simulator.generate_batch(count)

    saved_tweets = []
    for tweet_data in batch:
        result = analyzer.analyze(tweet_data["text"])
        tweet = Tweet(
            text=tweet_data["text"],
            username=tweet_data["username"],
            sentiment_score=result["score"],
            sentiment_label=result["label"],
            hashtags=json.dumps(tweet_data.get("hashtags", [])),
            mentions=json.dumps(tweet_data.get("mentions", [])),
        )
        db.add(tweet)
        saved_tweets.append(tweet)

    db.commit()
    for t in saved_tweets:
        db.refresh(t)

    # Record aggregate sentiment
    _record_sentiment_snapshot(db, saved_tweets)

    return {
        "tweets": [t.to_dict() for t in saved_tweets],
        "count": len(saved_tweets),
    }


@router.post("/tweets/generate")
def generate_tweets(
    count: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Generate a new batch of simulated tweets."""
    simulator = TweetStreamSimulator()
    batch = simulator.generate_batch(count)

    saved = []
    for tweet_data in batch:
        result = analyzer.analyze(tweet_data["text"])
        tweet = Tweet(
            text=tweet_data["text"],
            username=tweet_data["username"],
            sentiment_score=result["score"],
            sentiment_label=result["label"],
            hashtags=json.dumps(tweet_data.get("hashtags", [])),
            mentions=json.dumps(tweet_data.get("mentions", [])),
        )
        db.add(tweet)
        saved.append(tweet)

    db.commit()
    for t in saved:
        db.refresh(t)

    _record_sentiment_snapshot(db, saved)

    return {
        "generated": len(saved),
        "tweets": [t.to_dict() for t in saved],
    }


# ---------------------------------------------------------------------------
# Sentiment endpoints
# ---------------------------------------------------------------------------

@router.post("/analyze")
def analyze_text(req: AnalyzeRequest):
    """Analyze custom text for sentiment."""
    result = analyzer.analyze(req.text)
    return AnalyzeResponse(
        text=req.text,
        score=result["score"],
        label=result["label"],
        positive_words=result.get("positive_words", []),
        negative_words=result.get("negative_words", []),
        word_count=result.get("word_count", 0),
    )


@router.get("/sentiment/stats")
def sentiment_stats(db: Session = Depends(get_db)):
    """Get aggregate sentiment statistics."""
    total = db.query(func.count(Tweet.id)).scalar() or 0
    if total == 0:
        return SentimentStatsResponse()

    pos = db.query(func.count(Tweet.id)).filter(Tweet.sentiment_label == "positive").scalar() or 0
    neg = db.query(func.count(Tweet.id)).filter(Tweet.sentiment_label == "negative").scalar() or 0
    neu = db.query(func.count(Tweet.id)).filter(Tweet.sentiment_label == "neutral").scalar() or 0
    avg = db.query(func.avg(Tweet.sentiment_score)).scalar() or 0.0

    return SentimentStatsResponse(
        total_tweets=total,
        positive_count=pos,
        negative_count=neg,
        neutral_count=neu,
        avg_score=round(float(avg), 3),
        positive_pct=round(pos / total * 100, 1) if total else 0.0,
        negative_pct=round(neg / total * 100, 1) if total else 0.0,
        neutral_pct=round(neu / total * 100, 1) if total else 0.0,
    )


@router.get("/sentiment/history")
def sentiment_history(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Get sentiment history over time."""
    records = (
        db.query(SentimentRecord)
        .order_by(desc(SentimentRecord.timestamp))
        .limit(limit)
        .all()
    )
    records.reverse()
    return {
        "history": [r.to_dict() for r in records],
        "count": len(records),
    }


# ---------------------------------------------------------------------------
# Topic endpoints
# ---------------------------------------------------------------------------

@router.get("/topics")
def list_topics(db: Session = Depends(get_db)):
    """List all detected topics."""
    topics = db.query(Topic).order_by(desc(Topic.tweet_count)).all()
    return {"topics": [t.to_dict() for t in topics], "count": len(topics)}


@router.get("/topics/{topic_id}")
def get_topic(topic_id: int, db: Session = Depends(get_db)):
    """Get topic details with related tweets."""
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    tweets = (
        db.query(Tweet)
        .filter(Tweet.topic_id == topic_id)
        .order_by(desc(Tweet.created_at))
        .limit(50)
        .all()
    )

    return {
        "topic": topic.to_dict(),
        "tweets": [t.to_dict() for t in tweets],
    }


@router.post("/topics/cluster")
def run_clustering(db: Session = Depends(get_db)):
    """Run topic clustering on recent tweets."""
    tweets = db.query(Tweet).order_by(desc(Tweet.created_at)).limit(200).all()
    if not tweets:
        return {"topics": [], "message": "No tweets to cluster"}

    clusterer = TopicClusterer()
    tweet_dicts = [t.to_dict() for t in tweets]
    clusters = clusterer.cluster(tweet_dicts)

    created_topics = []
    for cluster_name, cluster_data in clusters.items():
        existing = db.query(Topic).filter(Topic.name == cluster_name).first()
        if existing:
            existing.tweet_count = cluster_data["count"]
            existing.avg_sentiment = cluster_data["avg_sentiment"]
            existing.keywords = json.dumps(cluster_data["keywords"])
            created_topics.append(existing)
        else:
            topic = Topic(
                name=cluster_name,
                keywords=json.dumps(cluster_data["keywords"]),
                tweet_count=cluster_data["count"],
                avg_sentiment=cluster_data["avg_sentiment"],
            )
            db.add(topic)
            created_topics.append(topic)

        # Assign tweets to topics
        for tweet_id in cluster_data.get("tweet_ids", []):
            tweet = db.query(Tweet).filter(Tweet.id == tweet_id).first()
            if tweet and existing:
                tweet.topic_id = existing.id
            elif tweet and created_topics:
                db.flush()
                tweet.topic_id = created_topics[-1].id

    db.commit()
    return {
        "topics": [t.to_dict() for t in created_topics],
        "count": len(created_topics),
    }


# ---------------------------------------------------------------------------
# Trend endpoints
# ---------------------------------------------------------------------------

@router.get("/trends")
def get_trends(db: Session = Depends(get_db)):
    """Get current trend data including sentiment history and top topics."""
    records = (
        db.query(SentimentRecord)
        .order_by(desc(SentimentRecord.timestamp))
        .limit(50)
        .all()
    )
    records.reverse()

    topics = db.query(Topic).order_by(desc(Topic.tweet_count)).limit(10).all()

    detector = TrendDetector()
    record_dicts = [r.to_dict() for r in records]
    alerts = detector.detect(record_dicts)

    return TrendResponse(
        sentiment_history=[r.to_dict() for r in records],
        volume_history=[
            {"timestamp": r.timestamp.isoformat() if r.timestamp else "",
             "count": r.total_count}
            for r in records
        ],
        top_topics=[t.to_dict() for t in topics],
        alerts=alerts,
    )


@router.get("/trends/alerts")
def get_alerts(db: Session = Depends(get_db)):
    """Get current volume and sentiment alerts."""
    records = (
        db.query(SentimentRecord)
        .order_by(desc(SentimentRecord.timestamp))
        .limit(50)
        .all()
    )
    records.reverse()

    detector = TrendDetector()
    record_dicts = [r.to_dict() for r in records]
    alerts = detector.detect(record_dicts)

    return {"alerts": [a.model_dump() for a in alerts], "count": len(alerts)}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _record_sentiment_snapshot(db: Session, tweets: list[Tweet]) -> None:
    """Record an aggregate sentiment measurement for the given tweets."""
    if not tweets:
        return

    scores = [t.sentiment_score for t in tweets]
    labels = [t.sentiment_label for t in tweets]

    pos = labels.count("positive")
    neg = labels.count("negative")
    neu = labels.count("neutral")
    avg = sum(scores) / len(scores) if scores else 0.0

    # Determine dominant topic
    topic_ids = [t.topic_id for t in tweets if t.topic_id]
    dominant = None
    if topic_ids:
        from collections import Counter
        most_common = Counter(topic_ids).most_common(1)
        if most_common:
            topic = db.query(Topic).filter(Topic.id == most_common[0][0]).first()
            if topic:
                dominant = topic.name

    record = SentimentRecord(
        avg_score=avg,
        positive_count=pos,
        negative_count=neg,
        neutral_count=neu,
        total_count=len(tweets),
        dominant_topic=dominant,
    )
    db.add(record)
    db.commit()
