"""HTML-serving routes for SentimentStream using Jinja2Templates."""

import os

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from models.database import get_db
from models.schemas import Tweet, Topic, SentimentRecord

_base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
templates = Jinja2Templates(directory=os.path.join(_base_dir, "templates"))

router = APIRouter(tags=["views"])


@router.get("/")
def index(request: Request, db: Session = Depends(get_db)):
    """Live stream dashboard -- main page."""
    recent_tweets = (
        db.query(Tweet).order_by(desc(Tweet.created_at)).limit(20).all()
    )
    total = db.query(func.count(Tweet.id)).scalar() or 0
    pos = db.query(func.count(Tweet.id)).filter(
        Tweet.sentiment_label == "positive"
    ).scalar() or 0
    neg = db.query(func.count(Tweet.id)).filter(
        Tweet.sentiment_label == "negative"
    ).scalar() or 0
    neu = db.query(func.count(Tweet.id)).filter(
        Tweet.sentiment_label == "neutral"
    ).scalar() or 0
    avg_score = db.query(func.avg(Tweet.sentiment_score)).scalar() or 0.0

    return templates.TemplateResponse("index.html", {
        "request": request,
        "tweets": [t.to_dict() for t in recent_tweets],
        "stats": {
            "total": total,
            "positive": pos,
            "negative": neg,
            "neutral": neu,
            "avg_score": round(float(avg_score), 3),
        },
    })


@router.get("/topics")
def topics_page(request: Request, db: Session = Depends(get_db)):
    """Topic clusters page."""
    topics = db.query(Topic).order_by(desc(Topic.tweet_count)).all()
    return templates.TemplateResponse("topics.html", {
        "request": request,
        "topics": [t.to_dict() for t in topics],
    })


@router.get("/trends")
def trends_page(request: Request, db: Session = Depends(get_db)):
    """Trend analysis page."""
    records = (
        db.query(SentimentRecord)
        .order_by(desc(SentimentRecord.timestamp))
        .limit(50)
        .all()
    )
    records.reverse()

    topics = db.query(Topic).order_by(desc(Topic.tweet_count)).limit(10).all()

    return templates.TemplateResponse("trends.html", {
        "request": request,
        "history": [r.to_dict() for r in records],
        "topics": [t.to_dict() for t in topics],
    })


@router.get("/analyze")
def analyze_page(request: Request):
    """Custom text analysis page."""
    return templates.TemplateResponse("analyze.html", {
        "request": request,
    })


@router.get("/about")
def about_page(request: Request, db: Session = Depends(get_db)):
    """About page with project information."""
    total = db.query(func.count(Tweet.id)).scalar() or 0
    topic_count = db.query(func.count(Topic.id)).scalar() or 0
    return templates.TemplateResponse("about.html", {
        "request": request,
        "total_tweets": total,
        "topic_count": topic_count,
    })
