"""Keyword-based sentiment analysis engine for SentimentStream.

Uses curated positive and negative word lists with modifier handling.
No external API calls required.
"""

import re
from typing import Any


# ---------------------------------------------------------------------------
# Word lists
# ---------------------------------------------------------------------------

POSITIVE_WORDS: set[str] = {
    "good", "great", "excellent", "amazing", "wonderful", "fantastic",
    "awesome", "brilliant", "outstanding", "superb", "love", "loved",
    "loving", "happy", "happily", "joy", "joyful", "delightful",
    "pleased", "glad", "thankful", "grateful", "blessed", "exciting",
    "excited", "beautiful", "gorgeous", "perfect", "best", "better",
    "incredible", "remarkable", "impressive", "magnificent", "marvelous",
    "phenomenal", "spectacular", "terrific", "fabulous", "splendid",
    "elegant", "graceful", "charming", "lovely", "pleasant", "nice",
    "fine", "cool", "sweet", "kind", "generous", "helpful", "friendly",
    "warm", "caring", "compassionate", "gentle", "inspiring", "inspired",
    "motivating", "uplifting", "encouraging", "hopeful", "optimistic",
    "positive", "confident", "strong", "brave", "courageous", "proud",
    "successful", "win", "winner", "victory", "triumph", "celebrate",
    "celebration", "achievement", "accomplished", "progress", "growth",
    "thrive", "flourish", "prosper", "bloom", "shine", "glow", "radiant",
    "vibrant", "lively", "energetic", "enthusiastic", "passionate",
    "innovative", "creative", "genius", "smart", "clever", "wise",
    "insightful", "revolutionary", "breakthrough", "transform",
    "recommend", "recommended", "approve", "endorsed", "trust", "reliable",
    "quality", "premium", "superior", "elite", "exceptional", "stellar",
}

NEGATIVE_WORDS: set[str] = {
    "bad", "terrible", "horrible", "awful", "dreadful", "disgusting",
    "hate", "hated", "hating", "angry", "furious", "outraged", "mad",
    "sad", "sadness", "depressed", "depressing", "miserable", "unhappy",
    "disappointed", "disappointing", "frustrating", "frustrated",
    "annoying", "annoyed", "irritating", "irritated", "ugly", "worst",
    "worse", "poor", "pathetic", "useless", "worthless", "stupid",
    "idiotic", "ridiculous", "absurd", "nonsense", "trash", "garbage",
    "waste", "fail", "failed", "failure", "disaster", "catastrophe",
    "crisis", "chaos", "mess", "broken", "damaged", "destroyed",
    "ruined", "corrupt", "corrupted", "toxic", "harmful", "dangerous",
    "threatening", "scary", "frightening", "terrifying", "horrifying",
    "shocking", "appalling", "atrocious", "abysmal", "inferior",
    "mediocre", "subpar", "lacking", "deficient", "flawed", "buggy",
    "slow", "sluggish", "laggy", "crash", "crashed", "error", "bug",
    "glitch", "problem", "issue", "complaint", "scam", "fraud", "fake",
    "dishonest", "deceptive", "misleading", "unfair", "unjust", "wrong",
    "evil", "cruel", "brutal", "vicious", "violent", "aggressive",
    "hostile", "rude", "disrespectful", "offensive", "inappropriate",
    "unacceptable", "intolerable", "unbearable", "painful", "suffering",
    "struggling", "hopeless", "desperate", "tragic", "heartbreaking",
    "devastating", "alarming", "concerning", "worrying", "troubling",
    "decline", "loss", "losing", "lost", "reject", "rejected", "deny",
    "denied", "block", "blocked", "ban", "banned", "censored",
}

INTENSIFIERS: set[str] = {
    "very", "extremely", "incredibly", "absolutely", "totally",
    "completely", "utterly", "really", "truly", "highly", "deeply",
    "especially", "particularly", "remarkably", "exceptionally",
    "extraordinarily", "immensely", "enormously", "supremely", "so",
}

NEGATORS: set[str] = {
    "not", "no", "never", "neither", "nor", "nobody", "nothing",
    "nowhere", "hardly", "barely", "scarcely", "rarely", "seldom",
    "don't", "doesn't", "didn't", "won't", "wouldn't", "couldn't",
    "shouldn't", "isn't", "aren't", "wasn't", "weren't", "cannot",
    "can't", "haven't", "hasn't", "hadn't",
}


# ---------------------------------------------------------------------------
# Analyzer
# ---------------------------------------------------------------------------

class SentimentAnalyzer:
    """Keyword-based sentiment analyzer with modifier support."""

    def __init__(
        self,
        positive_threshold: float = 0.2,
        negative_threshold: float = -0.2,
    ) -> None:
        self.positive_threshold = positive_threshold
        self.negative_threshold = negative_threshold
        self.positive_words = POSITIVE_WORDS
        self.negative_words = NEGATIVE_WORDS
        self.intensifiers = INTENSIFIERS
        self.negators = NEGATORS

    def tokenize(self, text: str) -> list[str]:
        """Tokenize and normalize text into lowercase words."""
        text = text.lower()
        text = re.sub(r"http\S+|www\.\S+", "", text)  # remove URLs
        text = re.sub(r"@\w+", "", text)  # remove mentions
        text = re.sub(r"#(\w+)", r"\1", text)  # keep hashtag text
        tokens = re.findall(r"[a-z']+", text)
        return tokens

    def analyze(self, text: str) -> dict[str, Any]:
        """Analyze text and return sentiment score, label, and details.

        Returns a dict with keys:
            score: float in [-1.0, 1.0]
            label: "positive", "negative", or "neutral"
            positive_words: list of matched positive words
            negative_words: list of matched negative words
            word_count: int
        """
        tokens = self.tokenize(text)
        if not tokens:
            return {
                "score": 0.0,
                "label": "neutral",
                "positive_words": [],
                "negative_words": [],
                "word_count": 0,
            }

        pos_found: list[str] = []
        neg_found: list[str] = []
        raw_score = 0.0

        for i, token in enumerate(tokens):
            # Check for negation in the previous 1-3 words
            is_negated = False
            lookback = min(i, 3)
            for j in range(1, lookback + 1):
                if tokens[i - j] in self.negators:
                    is_negated = True
                    break

            # Check for intensifier in the previous word
            is_intensified = False
            if i > 0 and tokens[i - 1] in self.intensifiers:
                is_intensified = True

            base_weight = 1.0
            if is_intensified:
                base_weight = 1.5

            if token in self.positive_words:
                if is_negated:
                    raw_score -= base_weight * 0.5
                    neg_found.append(token)
                else:
                    raw_score += base_weight
                    pos_found.append(token)
            elif token in self.negative_words:
                if is_negated:
                    raw_score += base_weight * 0.5
                    pos_found.append(token)
                else:
                    raw_score -= base_weight
                    neg_found.append(token)

        # Normalize score to [-1.0, 1.0]
        sentiment_words = len(pos_found) + len(neg_found)
        if sentiment_words > 0:
            normalized = raw_score / (sentiment_words + 1)
            score = max(-1.0, min(1.0, normalized))
        else:
            score = 0.0

        # Classify
        if score > self.positive_threshold:
            label = "positive"
        elif score < self.negative_threshold:
            label = "negative"
        else:
            label = "neutral"

        return {
            "score": round(score, 3),
            "label": label,
            "positive_words": list(set(pos_found)),
            "negative_words": list(set(neg_found)),
            "word_count": len(tokens),
        }

    def batch_analyze(self, texts: list[str]) -> list[dict[str, Any]]:
        """Analyze multiple texts and return list of results."""
        return [self.analyze(t) for t in texts]

    def get_word_sentiment(self, word: str) -> str:
        """Return the sentiment category of a single word."""
        w = word.lower().strip()
        if w in self.positive_words:
            return "positive"
        elif w in self.negative_words:
            return "negative"
        return "neutral"
