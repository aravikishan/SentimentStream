"""Service layer tests for SentimentStream."""

import pytest
from services.sentiment import SentimentAnalyzer
from services.stream import TweetStreamSimulator, TopicClusterer, TrendDetector
from models.schemas import TrendAlert


class TestSentimentAnalyzer:
    """Tests for the keyword-based sentiment analyzer."""

    def setup_method(self):
        self.analyzer = SentimentAnalyzer()

    def test_positive_text(self):
        """Clearly positive text is classified as positive."""
        result = self.analyzer.analyze("This is amazing and wonderful!")
        assert result["label"] == "positive"
        assert result["score"] > 0
        assert len(result["positive_words"]) > 0

    def test_negative_text(self):
        """Clearly negative text is classified as negative."""
        result = self.analyzer.analyze("This is terrible and awful!")
        assert result["label"] == "negative"
        assert result["score"] < 0
        assert len(result["negative_words"]) > 0

    def test_neutral_text(self):
        """Neutral text with no sentiment words is classified as neutral."""
        result = self.analyzer.analyze("The meeting is at three o clock.")
        assert result["label"] == "neutral"
        assert abs(result["score"]) <= 0.2

    def test_negation_handling(self):
        """Negation flips sentiment of following word."""
        result = self.analyzer.analyze("This is not good at all")
        # "not good" should contribute negative sentiment
        assert result["score"] < 0.2  # should not be positive

    def test_empty_text(self):
        """Empty text returns neutral with zero score."""
        result = self.analyzer.analyze("")
        assert result["label"] == "neutral"
        assert result["score"] == 0.0

    def test_batch_analyze(self):
        """Batch analysis returns correct number of results."""
        texts = ["Great!", "Terrible!", "Okay"]
        results = self.analyzer.batch_analyze(texts)
        assert len(results) == 3

    def test_word_sentiment(self):
        """Individual word sentiment lookup works."""
        assert self.analyzer.get_word_sentiment("amazing") == "positive"
        assert self.analyzer.get_word_sentiment("terrible") == "negative"
        assert self.analyzer.get_word_sentiment("table") == "neutral"


class TestTweetStreamSimulator:
    """Tests for the tweet stream simulator."""

    def test_generate_one(self):
        """Single tweet generation returns valid structure."""
        sim = TweetStreamSimulator(seed=42)
        tweet = sim.generate_one()
        assert "text" in tweet
        assert "username" in tweet
        assert "hashtags" in tweet
        assert tweet["username"].startswith("@")
        assert len(tweet["text"]) > 10

    def test_generate_batch(self):
        """Batch generation returns correct count."""
        sim = TweetStreamSimulator(seed=42)
        batch = sim.generate_batch(10)
        assert len(batch) == 10
        for tweet in batch:
            assert "text" in tweet
            assert "username" in tweet


class TestTopicClusterer:
    """Tests for the topic clustering engine."""

    def test_cluster_tweets(self):
        """Clustering assigns tweets to topics based on keywords."""
        clusterer = TopicClusterer()
        tweets = [
            {"text": "Great progress in AI and machine learning!", "hashtags": ["#AI", "#MachineLearning"], "sentiment_score": 0.5},
            {"text": "New React update is fantastic!", "hashtags": ["#React", "#JavaScript"], "sentiment_score": 0.6},
            {"text": "Docker and Kubernetes are essential", "hashtags": ["#Docker", "#Kubernetes"], "sentiment_score": 0.1},
        ]
        clusters = clusterer.cluster(tweets)
        assert isinstance(clusters, dict)
        # At least some tweets should be clustered
        total_clustered = sum(c["count"] for c in clusters.values())
        assert total_clustered > 0


class TestTrendDetector:
    """Tests for the trend detection engine."""

    def test_no_alerts_on_empty(self):
        """No alerts when records are empty."""
        detector = TrendDetector()
        alerts = detector.detect([])
        assert alerts == []

    def test_volume_spike_detection(self):
        """Volume spike is detected when recent volume exceeds threshold."""
        detector = TrendDetector(spike_multiplier=1.5)
        records = [
            {"total_count": 5, "avg_score": 0.0} for _ in range(10)
        ]
        # Add spike at end
        for _ in range(3):
            records.append({"total_count": 20, "avg_score": 0.0})

        alerts = detector.detect(records)
        spike_alerts = [a for a in alerts if a.alert_type == "volume_spike"]
        assert len(spike_alerts) > 0

    def test_sentiment_shift_detection(self):
        """Sentiment shift is detected on significant change."""
        detector = TrendDetector(sentiment_shift_threshold=0.3)
        records = [{"total_count": 5, "avg_score": -0.5} for _ in range(10)]
        # Add positive shift at end
        for _ in range(5):
            records.append({"total_count": 5, "avg_score": 0.8})

        alerts = detector.detect(records)
        shift_alerts = [a for a in alerts if a.alert_type == "sentiment_shift"]
        assert len(shift_alerts) > 0
