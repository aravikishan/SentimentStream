# SentimentStream

> Real-time social media sentiment analysis with simulated tweet streams,
> topic clustering, and trend detection.

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?logo=fastapi&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Tests](https://img.shields.io/badge/Tests-14%20passing-22c55e)
![Coverage](https://img.shields.io/badge/Coverage-92%25-22c55e)

---

## Overview

**SentimentStream** is a real-time social media sentiment analysis platform
that monitors a simulated tweet stream, classifies sentiment using a
keyword-based engine (no external API calls), clusters tweets into topics,
and detects emerging trends and sentiment shifts.

### Key Features

- **Live Tweet Stream** -- Continuously generates realistic simulated tweets
  with hashtags, mentions, and varied sentiment
- **Keyword-Based Sentiment Analysis** -- Positive / negative / neutral
  classification with confidence scores using curated word lists
- **Topic Clustering** -- Groups tweets by keyword frequency and
  co-occurrence patterns
- **Trend Detection** -- Identifies volume spikes, sentiment shifts, and
  emerging topics over sliding time windows
- **Interactive Dashboard** -- Auto-refreshing stream with sentiment gauge,
  topic bubble chart, and trend visualizations
- **Custom Text Analysis** -- Analyze any text for sentiment and extract
  key topics
- **REST API** -- Full JSON API for programmatic access to all features

---

## Architecture

```
sentimentstream/
|-- app.py                   # FastAPI entry point
|-- config.py                # App config, constants
|-- models/
|   |-- database.py          # SQLite setup with SQLAlchemy
|   |-- schemas.py           # ORM + Pydantic models
|-- routes/
|   |-- api.py               # REST API endpoints
|   |-- views.py             # HTML-serving routes (Jinja2)
|-- services/
|   |-- sentiment.py         # Keyword-based sentiment engine
|   |-- stream.py            # Tweet stream simulator + topic clustering
|-- templates/               # Jinja2 HTML templates
|-- static/
|   |-- css/style.css        # Twitter-inspired blue theme
|   |-- js/main.js           # Live updates, charts, gauges
|-- tests/                   # pytest test suite
|-- seed_data/data.json      # Sample tweets and topics
```

---

## Quick Start

### Prerequisites

- Python 3.11 or higher
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/sentimentstream.git
cd sentimentstream

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Start the server
chmod +x start.sh
./start.sh
```

The application will be available at `http://localhost:8009`.

### Docker

```bash
docker-compose up --build
```

---

## API Reference

### Stream Endpoints

| Method | Endpoint                | Description                      |
|--------|-------------------------|----------------------------------|
| GET    | `/api/tweets`           | List recent tweets (paginated)   |
| GET    | `/api/tweets/stream`    | Get latest batch from stream     |
| POST   | `/api/tweets/generate`  | Generate a new batch of tweets   |

### Sentiment Endpoints

| Method | Endpoint                | Description                      |
|--------|-------------------------|----------------------------------|
| POST   | `/api/analyze`          | Analyze custom text sentiment    |
| GET    | `/api/sentiment/stats`  | Aggregate sentiment statistics   |
| GET    | `/api/sentiment/history`| Sentiment over time              |

### Topic Endpoints

| Method | Endpoint                | Description                      |
|--------|-------------------------|----------------------------------|
| GET    | `/api/topics`           | List all detected topics         |
| GET    | `/api/topics/{id}`      | Topic details with related tweets|
| POST   | `/api/topics/cluster`   | Run topic clustering             |

### Trend Endpoints

| Method | Endpoint                | Description                      |
|--------|-------------------------|----------------------------------|
| GET    | `/api/trends`           | Current trend data               |
| GET    | `/api/trends/alerts`    | Volume and sentiment alerts      |

---

## Sentiment Analysis Engine

SentimentStream uses a keyword-based sentiment analysis engine with curated
word lists of ~100 positive and ~100 negative terms. The engine:

1. Tokenizes and normalizes input text
2. Matches tokens against positive and negative word lists
3. Applies modifier words (intensifiers, negations) for context
4. Computes a composite score in the range [-1.0, +1.0]
5. Classifies as positive (> 0.2), negative (< -0.2), or neutral

No external APIs or ML models are required.

---

## Topic Clustering

Topics are detected by:

1. Extracting hashtags and high-frequency keywords from the tweet stream
2. Computing keyword co-occurrence matrices
3. Grouping related keywords into topic clusters
4. Ranking topics by tweet volume and recency

---

## Trend Detection

Trends are identified by monitoring:

- **Volume spikes** -- Sudden increases in tweet frequency for a topic
- **Sentiment shifts** -- Significant changes in average sentiment
- **Emerging topics** -- New hashtags or keyword clusters gaining traction

Alerts are generated when metrics exceed configurable thresholds.

---

## Testing

```bash
# Run the full test suite
pytest tests/ -v --cov=. --cov-report=term-missing

# Run specific test modules
pytest tests/test_api.py -v
pytest tests/test_services.py -v
pytest tests/test_models.py -v
```

---

## Configuration

| Variable          | Default               | Description                     |
|-------------------|-----------------------|---------------------------------|
| `PORT`            | `8009`              | Server port                     |
| `SECRET_KEY`      | (dev key)             | Application secret key          |
| `DATABASE_URL`    | `sqlite:///...`       | Database connection string      |
| `DEBUG`           | `0`                   | Enable debug mode               |
| `STREAM_INTERVAL` | `2.0`                 | Seconds between stream batches  |
| `STREAM_BATCH_SIZE`| `5`                  | Tweets per batch                |

---

## Tech Stack

- **Backend:** Python 3.11+, FastAPI, SQLAlchemy, Pydantic
- **Frontend:** Jinja2 templates, vanilla JS, CSS3
- **Database:** SQLite
- **Testing:** pytest, httpx (async test client)
- **Deployment:** Docker, Docker Compose

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

*Built with FastAPI and Python. No external sentiment APIs required.*
