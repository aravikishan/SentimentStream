"""SentimentStream -- FastAPI application entry point.

A real-time social media sentiment analysis tool with simulated tweet
streams, topic clustering, and trend detection.
"""

import json
import logging
import os
import sys

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from config import settings
from models.database import create_tables, get_db, SessionLocal
from services.stream import TweetStreamSimulator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Global stream simulator instance
stream_simulator: TweetStreamSimulator | None = None


def seed_database() -> int:
    """Load seed data into the database if it is empty."""
    from models.schemas import Tweet, Topic
    from services.sentiment import SentimentAnalyzer

    db = SessionLocal()
    try:
        if db.query(Tweet).first() is not None:
            return 0

        seed_path = os.path.join(os.path.dirname(__file__), "seed_data", "data.json")
        if not os.path.exists(seed_path):
            return 0

        with open(seed_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)

        analyzer = SentimentAnalyzer()

        for topic_data in data.get("topics", []):
            topic = Topic(
                name=topic_data["name"],
                keywords=json.dumps(topic_data.get("keywords", [])),
                tweet_count=topic_data.get("tweet_count", 0),
                avg_sentiment=topic_data.get("avg_sentiment", 0.0),
            )
            db.add(topic)

        count = 0
        for tweet_data in data.get("tweets", []):
            result = analyzer.analyze(tweet_data["text"])
            tweet = Tweet(
                text=tweet_data["text"],
                username=tweet_data.get("username", "@user"),
                sentiment_score=result["score"],
                sentiment_label=result["label"],
                hashtags=json.dumps(tweet_data.get("hashtags", [])),
                mentions=json.dumps(tweet_data.get("mentions", [])),
            )
            db.add(tweet)
            count += 1

        db.commit()
        return count
    except Exception as exc:
        db.rollback()
        logger.warning("Could not seed database: %s", exc)
        return 0
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    global stream_simulator
    create_tables()
    seeded = seed_database()
    if seeded:
        logger.info("Seeded database with %d sample tweets", seeded)
    stream_simulator = TweetStreamSimulator()
    logger.info("SentimentStream started on port %d", settings.PORT)
    yield
    stream_simulator = None
    logger.info("SentimentStream shutting down")


def create_app() -> FastAPI:
    """Application factory -- create and configure the FastAPI app."""
    app = FastAPI(
        title="SentimentStream",
        description="Real-time social media sentiment analysis",
        version="1.0.0",
        lifespan=lifespan,
    )

    base_dir = os.path.dirname(os.path.abspath(__file__))
    static_dir = os.path.join(base_dir, "static")
    os.makedirs(static_dir, exist_ok=True)
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    from routes.api import router as api_router
    from routes.views import router as views_router

    app.include_router(api_router)
    app.include_router(views_router)

    return app


app = create_app()
