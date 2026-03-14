"""Tweet stream simulator, topic clustering, and trend detection.

Generates realistic simulated tweets with hashtags, mentions, and
varied sentiment. Provides topic clustering by keyword frequency
and co-occurrence, and trend detection via volume/sentiment analysis.
"""

import json
import random
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Optional

from models.schemas import TrendAlert


# ---------------------------------------------------------------------------
# Tweet templates and data
# ---------------------------------------------------------------------------

USERNAMES = [
    "@tech_insider", "@data_nerd", "@news_daily", "@crypto_watcher",
    "@ai_enthusiast", "@startup_life", "@dev_thoughts", "@market_pulse",
    "@science_now", "@digital_nomad", "@code_master", "@web3_builder",
    "@green_future", "@health_tech", "@gaming_world", "@music_vibes",
    "@travel_tales", "@food_critic", "@sports_fan", "@movie_buff",
    "@book_worm", "@fitness_guru", "@photo_grapher", "@design_hub",
    "@cyber_sec", "@cloud_ops", "@mobile_dev", "@open_source",
    "@ml_engineer", "@product_mgr",
]

HASHTAGS = [
    "#AI", "#MachineLearning", "#Python", "#JavaScript", "#React",
    "#DataScience", "#CloudComputing", "#Cybersecurity", "#Blockchain",
    "#IoT", "#5G", "#QuantumComputing", "#AR", "#VR", "#Metaverse",
    "#Sustainability", "#CleanEnergy", "#ElectricVehicles", "#SpaceTech",
    "#HealthTech", "#EdTech", "#FinTech", "#GameDev", "#OpenSource",
    "#DevOps", "#API", "#Microservices", "#Docker", "#Kubernetes",
    "#TechNews", "#Innovation", "#Startup", "#Coding", "#WebDev",
    "#MobileDev", "#UXDesign", "#BigData", "#Analytics", "#Automation",
    "#RPA", "#NLP", "#ComputerVision", "#DeepLearning", "#Neural",
]

POSITIVE_TEMPLATES = [
    "Just discovered {hashtag} and it's absolutely amazing! The future is here.",
    "Incredible progress in {hashtag} today! So excited about what's coming next.",
    "Love how {hashtag} is transforming the industry. Great work by the community!",
    "The new {hashtag} release is fantastic! Best update in years {hashtag2}",
    "Really impressed with the {hashtag} presentation. Outstanding innovation!",
    "Happy to announce our team won the {hashtag} hackathon! {hashtag2}",
    "This {hashtag} tutorial is brilliant! Finally understand the concepts.",
    "Wonderful news for {hashtag} developers! The ecosystem keeps getting better.",
    "Excited to share my new {hashtag} project! Built with love and passion.",
    "The {hashtag} community is so welcoming and helpful. Grateful to be part of it!",
    "Successfully deployed our {hashtag} solution! The results are impressive.",
    "Best conference talk on {hashtag} I've ever seen. Truly inspiring!",
    "Our {hashtag} adoption has been phenomenal. Outstanding team effort!",
    "Thrilled about the {hashtag} partnership announcement! Great things ahead.",
    "Just shipped a beautiful {hashtag} feature. The team did an excellent job!",
]

NEGATIVE_TEMPLATES = [
    "Another {hashtag} outage today. This is becoming unacceptable.",
    "Frustrated with the {hashtag} API changes. Everything is broken again.",
    "The new {hashtag} update is terrible. So many bugs and crashes. {hashtag2}",
    "Disappointed by the {hashtag} security breach. Users deserve better.",
    "Why is {hashtag} still so slow and unreliable? This is ridiculous.",
    "Lost hours debugging {hashtag} issues. The documentation is awful.",
    "The {hashtag} pricing changes are unfair to small developers. {hashtag2}",
    "Horrible experience with {hashtag} support. No response for weeks.",
    "The {hashtag} community toxicity is getting worse. We need to do better.",
    "Another failed {hashtag} deployment. This tool is so frustrating.",
    "Worried about {hashtag} privacy concerns. The data handling is problematic.",
    "The decline of {hashtag} quality is alarming. Standards are dropping.",
    "Can't believe {hashtag} removed essential features. Terrible decision.",
    "Struggling with {hashtag} compatibility issues. Nothing works properly.",
    "The {hashtag} layoffs are devastating. So many talented people affected.",
]

NEUTRAL_TEMPLATES = [
    "New {hashtag} report released today. Some interesting data points.",
    "Attending the {hashtag} conference next week. Anyone else going?",
    "Updated my {hashtag} environment to the latest version. {hashtag2}",
    "Reading about {hashtag} trends for 2024. The landscape is changing.",
    "Working on a {hashtag} proof of concept this week. {hashtag2}",
    "The {hashtag} market analysis shows mixed signals. Worth watching.",
    "Comparing {hashtag} frameworks for our next project. {hashtag2}",
    "Published a new blog post about {hashtag} architecture patterns.",
    "Our team is evaluating {hashtag} solutions for the upcoming quarter.",
    "Interesting {hashtag} discussion on the forum today. Different perspectives.",
    "Looking at {hashtag} certification options. Any recommendations?",
    "The {hashtag} survey results are in. Let me share the key findings.",
    "Running benchmarks on {hashtag} vs alternative approaches. {hashtag2}",
    "Setting up {hashtag} monitoring for our infrastructure. {hashtag2}",
    "The {hashtag} roadmap for next year was just announced. Notable changes.",
]

MENTIONS = [
    "@elonmusk", "@sundarpichai", "@satloving", "@tim_cook",
    "@jeffbezos", "@billgates", "@jack", "@sheraborny",
    "@demaboris", "@real_developer", "@open_ai", "@google",
    "@microsoft", "@amazon_tech", "@github", "@vercel",
]


# ---------------------------------------------------------------------------
# Stream Simulator
# ---------------------------------------------------------------------------

class TweetStreamSimulator:
    """Generates realistic simulated tweets with varied sentiment."""

    def __init__(self, seed: Optional[int] = None) -> None:
        if seed is not None:
            random.seed(seed)
        self._counter = 0

    def _pick_hashtags(self, count: int = 2) -> list[str]:
        """Pick random hashtags."""
        return random.sample(HASHTAGS, min(count, len(HASHTAGS)))

    def _pick_username(self) -> str:
        """Pick a random username."""
        return random.choice(USERNAMES)

    def _pick_mention(self) -> str:
        """Pick a random mention."""
        return random.choice(MENTIONS)

    def generate_one(self) -> dict[str, Any]:
        """Generate a single simulated tweet."""
        self._counter += 1
        sentiment_roll = random.random()

        # 40% positive, 30% negative, 30% neutral
        if sentiment_roll < 0.4:
            template = random.choice(POSITIVE_TEMPLATES)
        elif sentiment_roll < 0.7:
            template = random.choice(NEGATIVE_TEMPLATES)
        else:
            template = random.choice(NEUTRAL_TEMPLATES)

        hashtags = self._pick_hashtags(random.randint(1, 3))
        username = self._pick_username()

        text = template.replace("{hashtag}", hashtags[0])
        if len(hashtags) > 1:
            text = text.replace("{hashtag2}", hashtags[1])
        else:
            text = text.replace("{hashtag2}", "")

        # Sometimes add a mention
        if random.random() < 0.3:
            mention = self._pick_mention()
            text = f"{text} cc {mention}"
        else:
            mention = None

        # Extract all hashtags and mentions from the final text
        found_hashtags = re.findall(r"#\w+", text)
        found_mentions = re.findall(r"@\w+", text)

        return {
            "text": text.strip(),
            "username": username,
            "hashtags": found_hashtags,
            "mentions": found_mentions,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def generate_batch(self, count: int = 5) -> list[dict[str, Any]]:
        """Generate a batch of simulated tweets."""
        return [self.generate_one() for _ in range(count)]


# ---------------------------------------------------------------------------
# Topic Clusterer
# ---------------------------------------------------------------------------

class TopicClusterer:
    """Clusters tweets into topics based on keyword frequency and co-occurrence."""

    # Map of topic names to their defining keywords
    TOPIC_DEFINITIONS: dict[str, list[str]] = {
        "Artificial Intelligence": [
            "ai", "machinelearning", "deeplearning", "neural",
            "nlp", "computervision", "ml",
        ],
        "Web Development": [
            "javascript", "react", "webdev", "frontend", "backend",
            "api", "html", "css", "node", "typescript",
        ],
        "Cloud & DevOps": [
            "cloudcomputing", "devops", "docker", "kubernetes",
            "microservices", "aws", "azure", "gcp", "cloud",
        ],
        "Cybersecurity": [
            "cybersecurity", "security", "privacy", "breach",
            "hacking", "infosec", "vulnerability",
        ],
        "Data Science": [
            "datascience", "bigdata", "analytics", "data",
            "python", "statistics", "visualization",
        ],
        "Blockchain & Crypto": [
            "blockchain", "crypto", "bitcoin", "ethereum",
            "web3", "defi", "nft",
        ],
        "Emerging Tech": [
            "iot", "5g", "quantumcomputing", "ar", "vr",
            "metaverse", "spacetech",
        ],
        "Green Tech": [
            "sustainability", "cleanenergy", "electricvehicles",
            "green", "renewable", "solar", "climate",
        ],
        "Game Development": [
            "gamedev", "gaming", "unity", "unreal",
            "indiegame", "esports",
        ],
        "Career & Community": [
            "opensource", "coding", "startup", "innovation",
            "tech", "developer", "community",
        ],
    }

    def _extract_keywords(self, tweet: dict) -> list[str]:
        """Extract lowercase keywords from a tweet."""
        keywords = []
        # Extract from hashtags
        for ht in tweet.get("hashtags", []):
            clean = ht.lstrip("#").lower()
            keywords.append(clean)
        # Extract notable words from text
        text = tweet.get("text", "").lower()
        text = re.sub(r"http\S+|www\.\S+", "", text)
        text = re.sub(r"@\w+", "", text)
        text = re.sub(r"#(\w+)", r"\1", text)
        words = re.findall(r"[a-z]+", text)
        # Keep words longer than 3 characters as potential keywords
        keywords.extend(w for w in words if len(w) > 3)
        return keywords

    def cluster(self, tweets: list[dict]) -> dict[str, dict[str, Any]]:
        """Cluster tweets into topics and return topic data.

        Returns a dict mapping topic names to:
            keywords: list[str]
            count: int
            avg_sentiment: float
            tweet_ids: list[int]
        """
        topic_tweets: dict[str, list[dict]] = defaultdict(list)
        topic_keywords: dict[str, Counter] = defaultdict(Counter)

        for tweet in tweets:
            kws = self._extract_keywords(tweet)
            matched_topic = self._match_topic(kws)
            if matched_topic:
                topic_tweets[matched_topic].append(tweet)
                topic_keywords[matched_topic].update(kws)

        results: dict[str, dict[str, Any]] = {}
        for topic_name, tweet_list in topic_tweets.items():
            scores = [
                t.get("sentiment_score", 0.0) for t in tweet_list
            ]
            avg_sent = sum(scores) / len(scores) if scores else 0.0
            top_kws = [
                kw for kw, _ in topic_keywords[topic_name].most_common(10)
            ]
            tweet_ids = [t.get("id") for t in tweet_list if t.get("id")]

            results[topic_name] = {
                "keywords": top_kws,
                "count": len(tweet_list),
                "avg_sentiment": round(avg_sent, 3),
                "tweet_ids": tweet_ids,
            }

        return results

    def _match_topic(self, keywords: list[str]) -> Optional[str]:
        """Match a set of keywords to the best topic definition."""
        best_topic = None
        best_score = 0

        for topic_name, topic_kws in self.TOPIC_DEFINITIONS.items():
            overlap = sum(1 for kw in keywords if kw in topic_kws)
            if overlap > best_score:
                best_score = overlap
                best_topic = topic_name

        return best_topic if best_score > 0 else None

    def get_cooccurrence(self, tweets: list[dict]) -> dict[str, dict[str, int]]:
        """Compute keyword co-occurrence matrix from tweets."""
        cooccurrence: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

        for tweet in tweets:
            kws = list(set(self._extract_keywords(tweet)))
            for i, kw1 in enumerate(kws):
                for kw2 in kws[i + 1:]:
                    cooccurrence[kw1][kw2] += 1
                    cooccurrence[kw2][kw1] += 1

        return dict(cooccurrence)


# ---------------------------------------------------------------------------
# Trend Detector
# ---------------------------------------------------------------------------

class TrendDetector:
    """Detects volume spikes, sentiment shifts, and emerging trends."""

    def __init__(
        self,
        window_size: int = 20,
        spike_multiplier: float = 1.5,
        sentiment_shift_threshold: float = 0.3,
    ) -> None:
        self.window_size = window_size
        self.spike_multiplier = spike_multiplier
        self.sentiment_shift_threshold = sentiment_shift_threshold

    def detect(self, records: list[dict]) -> list[TrendAlert]:
        """Analyze sentiment records and return trend alerts."""
        alerts: list[TrendAlert] = []

        if len(records) < 3:
            return alerts

        # Volume spike detection
        volume_alerts = self._detect_volume_spikes(records)
        alerts.extend(volume_alerts)

        # Sentiment shift detection
        shift_alerts = self._detect_sentiment_shifts(records)
        alerts.extend(shift_alerts)

        # Overall mood alerts
        mood_alerts = self._detect_mood_extremes(records)
        alerts.extend(mood_alerts)

        return alerts

    def _detect_volume_spikes(self, records: list[dict]) -> list[TrendAlert]:
        """Detect sudden increases in tweet volume."""
        alerts: list[TrendAlert] = []
        volumes = [r.get("total_count", 0) for r in records]

        if len(volumes) < 5:
            return alerts

        # Compare recent volume to historical average
        recent = volumes[-3:]
        historical = volumes[:-3]

        if not historical:
            return alerts

        avg_historical = sum(historical) / len(historical)
        avg_recent = sum(recent) / len(recent)

        if avg_historical > 0 and avg_recent > avg_historical * self.spike_multiplier:
            ratio = round(avg_recent / avg_historical, 1)
            alerts.append(TrendAlert(
                alert_type="volume_spike",
                message=f"Tweet volume increased {ratio}x above average",
                severity="warning",
                value=avg_recent,
            ))

        return alerts

    def _detect_sentiment_shifts(self, records: list[dict]) -> list[TrendAlert]:
        """Detect significant changes in average sentiment."""
        alerts: list[TrendAlert] = []
        scores = [r.get("avg_score", 0.0) for r in records]

        if len(scores) < 5:
            return alerts

        # Compare recent sentiment to historical
        recent_avg = sum(scores[-5:]) / 5
        historical_avg = sum(scores[:-5]) / len(scores[:-5]) if len(scores) > 5 else 0.0

        shift = recent_avg - historical_avg

        if abs(shift) > self.sentiment_shift_threshold:
            direction = "positive" if shift > 0 else "negative"
            severity = "warning" if abs(shift) > 0.5 else "info"
            alerts.append(TrendAlert(
                alert_type="sentiment_shift",
                message=f"Sentiment shifting {direction} (change: {shift:+.3f})",
                severity=severity,
                value=round(shift, 3),
            ))

        return alerts

    def _detect_mood_extremes(self, records: list[dict]) -> list[TrendAlert]:
        """Detect when overall mood reaches extreme levels."""
        alerts: list[TrendAlert] = []

        if not records:
            return alerts

        latest = records[-1]
        avg_score = latest.get("avg_score", 0.0)

        if avg_score > 0.6:
            alerts.append(TrendAlert(
                alert_type="mood_extreme",
                message="Overall sentiment is highly positive",
                severity="info",
                value=round(avg_score, 3),
            ))
        elif avg_score < -0.6:
            alerts.append(TrendAlert(
                alert_type="mood_extreme",
                message="Overall sentiment is highly negative",
                severity="warning",
                value=round(avg_score, 3),
            ))

        # Check if negative tweets dominate
        neg = latest.get("negative_count", 0)
        total = latest.get("total_count", 0)
        if total > 0 and neg / total > 0.6:
            alerts.append(TrendAlert(
                alert_type="negativity_surge",
                message=f"Negative tweets dominate ({neg}/{total} = {neg/total:.0%})",
                severity="warning",
                value=round(neg / total, 3),
            ))

        return alerts
