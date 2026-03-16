/* SentimentStream -- Main JavaScript
   Live stream updates, sentiment gauge, topic bubble chart, trend charts
*/

let streamActive = false;
let streamInterval = null;
const STREAM_DELAY = 3000;

// ---------------------------------------------------------------------------
// Stream controls
// ---------------------------------------------------------------------------

function toggleStream() {
    const btn = document.getElementById("btn-stream");
    const dot = document.getElementById("stream-dot");
    const statusText = document.getElementById("stream-status-text");

    if (streamActive) {
        clearInterval(streamInterval);
        streamInterval = null;
        streamActive = false;
        btn.textContent = "Start Stream";
        dot.classList.remove("active");
        statusText.textContent = "Stream paused";
    } else {
        streamActive = true;
        btn.textContent = "Stop Stream";
        dot.classList.add("active");
        statusText.textContent = "Stream active";
        fetchBatch();
        streamInterval = setInterval(fetchBatch, STREAM_DELAY);
    }
}

function fetchBatch() {
    fetch("/api/tweets/stream?count=5")
        .then(function(r) { return r.json(); })
        .then(function(data) {
            if (data.tweets && data.tweets.length > 0) {
                prependTweets(data.tweets);
                updateStats();
                updateGauge();
            }
        })
        .catch(function(err) { console.error("Stream error:", err); });
}

function generateTweets(count) {
    fetch("/api/tweets/generate?count=" + count, { method: "POST" })
        .then(function(r) { return r.json(); })
        .then(function(data) {
            if (data.tweets && data.tweets.length > 0) {
                prependTweets(data.tweets);
                updateStats();
                updateGauge();
            }
        })
        .catch(function(err) { console.error("Generate error:", err); });
}

// ---------------------------------------------------------------------------
// Tweet rendering
// ---------------------------------------------------------------------------

function prependTweets(tweets) {
    var container = document.getElementById("tweet-stream");
    if (!container) return;

    tweets.forEach(function(tweet) {
        var div = document.createElement("div");
        div.className = "tweet-item sentiment-" + tweet.sentiment_label;
        div.style.opacity = "0";
        div.style.transform = "translateY(-10px)";

        var hashtags = "";
        if (tweet.hashtags) {
            tweet.hashtags.forEach(function(tag) {
                hashtags += '<span class="hashtag">' + escapeHtml(tag) + "</span> ";
            });
        }

        div.innerHTML =
            '<div class="tweet-header">' +
                '<span class="tweet-username">' + escapeHtml(tweet.username) + "</span>" +
                '<span class="tweet-sentiment badge-' + tweet.sentiment_label + '">' +
                    tweet.sentiment_label + " (" + tweet.sentiment_score + ")" +
                "</span>" +
            "</div>" +
            '<div class="tweet-text">' + escapeHtml(tweet.text) + "</div>" +
            '<div class="tweet-meta">' + hashtags +
                '<span class="tweet-time">' + formatTime(tweet.created_at) + "</span>" +
            "</div>";

        container.insertBefore(div, container.firstChild);

        // Animate in
        requestAnimationFrame(function() {
            div.style.transition = "opacity 0.3s, transform 0.3s";
            div.style.opacity = "1";
            div.style.transform = "translateY(0)";
        });
    });

    // Update counter
    var counter = document.getElementById("stream-counter");
    if (counter) {
        var count = container.querySelectorAll(".tweet-item").length;
        counter.textContent = count + " tweets";
    }

    // Limit visible tweets
    var items = container.querySelectorAll(".tweet-item");
    if (items.length > 100) {
        for (var i = 100; i < items.length; i++) {
            items[i].remove();
        }
    }
}

function applyFilter() {
    var filter = document.getElementById("sentiment-filter").value;
    var items = document.querySelectorAll(".tweet-item");
    items.forEach(function(item) {
        if (!filter) {
            item.style.display = "";
        } else if (item.classList.contains("sentiment-" + filter)) {
            item.style.display = "";
        } else {
            item.style.display = "none";
        }
    });
}

// ---------------------------------------------------------------------------
// Stats update
// ---------------------------------------------------------------------------

function updateStats() {
    fetch("/api/sentiment/stats")
        .then(function(r) { return r.json(); })
        .then(function(data) {
            setTextIfExists("total-tweets", data.total_tweets);
            setTextIfExists("positive-count", data.positive_count);
            setTextIfExists("negative-count", data.negative_count);
            setTextIfExists("neutral-count", data.neutral_count);
        })
        .catch(function() {});
}

// ---------------------------------------------------------------------------
// Sentiment Gauge (canvas arc)
// ---------------------------------------------------------------------------

function drawGauge(canvasId, score) {
    var canvas = document.getElementById(canvasId);
    if (!canvas) return;

    var ctx = canvas.getContext("2d");
    var W = canvas.width;
    var H = canvas.height;
    var cx = W / 2;
    var cy = H - 10;
    var radius = Math.min(cx, cy) - 20;

    ctx.clearRect(0, 0, W, H);

    // Background arc
    ctx.beginPath();
    ctx.arc(cx, cy, radius, Math.PI, 0, false);
    ctx.lineWidth = 18;
    ctx.strokeStyle = "#38444D";
    ctx.stroke();

    // Gradient arcs: red -> yellow -> green
    var segments = [
        { start: Math.PI, end: Math.PI + Math.PI * 0.33, color: "#E0245E" },
        { start: Math.PI + Math.PI * 0.33, end: Math.PI + Math.PI * 0.66, color: "#FFAD1F" },
        { start: Math.PI + Math.PI * 0.66, end: Math.PI * 2, color: "#17BF63" },
    ];

    segments.forEach(function(seg) {
        ctx.beginPath();
        ctx.arc(cx, cy, radius, seg.start, seg.end, false);
        ctx.lineWidth = 18;
        ctx.strokeStyle = seg.color;
        ctx.globalAlpha = 0.3;
        ctx.stroke();
        ctx.globalAlpha = 1.0;
    });

    // Needle
    var normalizedScore = (parseFloat(score) + 1) / 2;  // 0 to 1
    normalizedScore = Math.max(0, Math.min(1, normalizedScore));
    var angle = Math.PI + normalizedScore * Math.PI;

    var needleLen = radius - 10;
    var nx = cx + needleLen * Math.cos(angle);
    var ny = cy + needleLen * Math.sin(angle);

    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.lineTo(nx, ny);
    ctx.lineWidth = 3;
    ctx.strokeStyle = "#1DA1F2";
    ctx.stroke();

    // Center dot
    ctx.beginPath();
    ctx.arc(cx, cy, 6, 0, Math.PI * 2);
    ctx.fillStyle = "#1DA1F2";
    ctx.fill();
}

function updateGauge() {
    fetch("/api/sentiment/stats")
        .then(function(r) { return r.json(); })
        .then(function(data) {
            var scoreEl = document.getElementById("gauge-score");
            if (scoreEl) scoreEl.textContent = data.avg_score.toFixed(3);
            drawGauge("sentiment-gauge", data.avg_score);
        })
        .catch(function() {});
}

// ---------------------------------------------------------------------------
// Topic Bubble Chart
// ---------------------------------------------------------------------------

function drawTopicBubbles(topics) {
    var canvas = document.getElementById("topic-bubbles");
    if (!canvas || !topics || topics.length === 0) return;

    var ctx = canvas.getContext("2d");
    var W = canvas.width;
    var H = canvas.height;
    ctx.clearRect(0, 0, W, H);

    var maxCount = Math.max.apply(null, topics.map(function(t) { return t.tweet_count || 1; }));

    topics.forEach(function(topic, i) {
        var ratio = (topic.tweet_count || 1) / maxCount;
        var r = 20 + ratio * 50;

        // Layout in rows
        var cols = Math.ceil(Math.sqrt(topics.length));
        var row = Math.floor(i / cols);
        var col = i % cols;
        var spacingX = W / (cols + 1);
        var spacingY = H / (Math.ceil(topics.length / cols) + 1);
        var x = spacingX * (col + 1);
        var y = spacingY * (row + 1);

        // Color by sentiment
        var color;
        if (topic.avg_sentiment > 0.2) {
            color = "rgba(23, 191, 99, 0.6)";
        } else if (topic.avg_sentiment < -0.2) {
            color = "rgba(224, 36, 94, 0.6)";
        } else {
            color = "rgba(29, 161, 242, 0.6)";
        }

        ctx.beginPath();
        ctx.arc(x, y, r, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();
        ctx.strokeStyle = color.replace("0.6", "0.9");
        ctx.lineWidth = 2;
        ctx.stroke();

        // Label
        ctx.fillStyle = "#FFFFFF";
        ctx.font = "bold 11px sans-serif";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";

        var label = topic.name;
        if (label.length > 14) label = label.substring(0, 12) + "..";
        ctx.fillText(label, x, y - 6);
        ctx.font = "10px sans-serif";
        ctx.fillStyle = "#AAB8C2";
        ctx.fillText(topic.tweet_count + " tweets", x, y + 10);
    });
}

// ---------------------------------------------------------------------------
// Trend Charts (simple canvas line/bar charts)
// ---------------------------------------------------------------------------

function drawSentimentChart(history) {
    var canvas = document.getElementById("sentiment-chart");
    if (!canvas || history.length === 0) return;

    var ctx = canvas.getContext("2d");
    var W = canvas.width;
    var H = canvas.height;
    var padding = { top: 20, right: 20, bottom: 30, left: 50 };
    var chartW = W - padding.left - padding.right;
    var chartH = H - padding.top - padding.bottom;

    ctx.clearRect(0, 0, W, H);

    // Y axis: -1 to 1
    var yMin = -1, yMax = 1;

    // Draw grid
    ctx.strokeStyle = "#38444D";
    ctx.lineWidth = 1;
    for (var g = 0; g <= 4; g++) {
        var gy = padding.top + (g / 4) * chartH;
        ctx.beginPath();
        ctx.moveTo(padding.left, gy);
        ctx.lineTo(W - padding.right, gy);
        ctx.stroke();

        ctx.fillStyle = "#8899A6";
        ctx.font = "11px sans-serif";
        ctx.textAlign = "right";
        var label = (yMax - (g / 4) * (yMax - yMin)).toFixed(1);
        ctx.fillText(label, padding.left - 8, gy + 4);
    }

    // Zero line
    var zeroY = padding.top + (yMax / (yMax - yMin)) * chartH;
    ctx.strokeStyle = "#8899A6";
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(padding.left, zeroY);
    ctx.lineTo(W - padding.right, zeroY);
    ctx.stroke();
    ctx.setLineDash([]);

    // Plot line
    ctx.beginPath();
    ctx.strokeStyle = "#1DA1F2";
    ctx.lineWidth = 2;
    history.forEach(function(record, i) {
        var x = padding.left + (i / (history.length - 1 || 1)) * chartW;
        var normalized = (record.avg_score - yMin) / (yMax - yMin);
        var y = padding.top + (1 - normalized) * chartH;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    });
    ctx.stroke();

    // Dots
    history.forEach(function(record, i) {
        var x = padding.left + (i / (history.length - 1 || 1)) * chartW;
        var normalized = (record.avg_score - yMin) / (yMax - yMin);
        var y = padding.top + (1 - normalized) * chartH;

        ctx.beginPath();
        ctx.arc(x, y, 3, 0, Math.PI * 2);
        if (record.avg_score > 0.2) ctx.fillStyle = "#17BF63";
        else if (record.avg_score < -0.2) ctx.fillStyle = "#E0245E";
        else ctx.fillStyle = "#AAB8C2";
        ctx.fill();
    });
}

function drawVolumeChart(history) {
    var canvas = document.getElementById("volume-chart");
    if (!canvas || history.length === 0) return;

    var ctx = canvas.getContext("2d");
    var W = canvas.width;
    var H = canvas.height;
    var padding = { top: 20, right: 20, bottom: 30, left: 50 };
    var chartW = W - padding.left - padding.right;
    var chartH = H - padding.top - padding.bottom;

    ctx.clearRect(0, 0, W, H);

    var maxVol = Math.max.apply(null, history.map(function(r) { return r.total_count || 0; }));
    if (maxVol === 0) maxVol = 1;

    var barWidth = Math.max(4, (chartW / history.length) - 2);

    history.forEach(function(record, i) {
        var x = padding.left + (i / history.length) * chartW;
        var h = (record.total_count / maxVol) * chartH;
        var y = padding.top + chartH - h;

        ctx.fillStyle = "rgba(29, 161, 242, 0.6)";
        ctx.fillRect(x, y, barWidth, h);
    });

    // Y axis labels
    ctx.fillStyle = "#8899A6";
    ctx.font = "11px sans-serif";
    ctx.textAlign = "right";
    ctx.fillText(maxVol.toString(), padding.left - 8, padding.top + 10);
    ctx.fillText("0", padding.left - 8, padding.top + chartH + 4);
}

// ---------------------------------------------------------------------------
// Alerts
// ---------------------------------------------------------------------------

function loadAlerts() {
    fetch("/api/trends/alerts")
        .then(function(r) { return r.json(); })
        .then(function(data) {
            var container = document.getElementById("alerts-list");
            if (!container) return;

            if (!data.alerts || data.alerts.length === 0) {
                container.innerHTML = '<p class="loading-text">No active alerts</p>';
                return;
            }

            container.innerHTML = "";
            data.alerts.forEach(function(alert) {
                var div = document.createElement("div");
                div.className = "alert-item alert-" + (alert.severity || "info");
                div.innerHTML =
                    '<div class="alert-type">' + escapeHtml(alert.alert_type) + "</div>" +
                    '<div>' + escapeHtml(alert.message) + "</div>";
                container.appendChild(div);
            });
        })
        .catch(function() {
            var container = document.getElementById("alerts-list");
            if (container) container.innerHTML = '<p class="loading-text">Could not load alerts</p>';
        });
}

// ---------------------------------------------------------------------------
// Analyze page
// ---------------------------------------------------------------------------

function analyzeText(event) {
    event.preventDefault();
    var input = document.getElementById("analyze-input");
    var text = input.value.trim();
    if (!text) return;

    fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: text }),
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
        var card = document.getElementById("results-card");
        card.style.display = "block";

        document.getElementById("result-score").textContent = data.score.toFixed(3);
        var labelEl = document.getElementById("result-label");
        labelEl.textContent = data.label;
        labelEl.className = "result-label";
        if (data.label === "positive") labelEl.style.color = "#17BF63";
        else if (data.label === "negative") labelEl.style.color = "#E0245E";
        else labelEl.style.color = "#AAB8C2";

        document.getElementById("result-word-count").textContent = data.word_count;

        var posContainer = document.getElementById("positive-words");
        posContainer.innerHTML = "";
        (data.positive_words || []).forEach(function(w) {
            var span = document.createElement("span");
            span.className = "word-tag-pos";
            span.textContent = w;
            posContainer.appendChild(span);
        });

        var negContainer = document.getElementById("negative-words");
        negContainer.innerHTML = "";
        (data.negative_words || []).forEach(function(w) {
            var span = document.createElement("span");
            span.className = "word-tag-neg";
            span.textContent = w;
            negContainer.appendChild(span);
        });

        drawGauge("result-gauge", data.score);
    })
    .catch(function(err) { console.error("Analyze error:", err); });
}

function setExample(text) {
    var input = document.getElementById("analyze-input");
    if (input) {
        input.value = text;
        updateCharCount();
    }
}

function updateCharCount() {
    var input = document.getElementById("analyze-input");
    var counter = document.getElementById("char-counter");
    if (input && counter) {
        counter.textContent = input.value.length;
    }
}

// ---------------------------------------------------------------------------
// Topic clustering trigger
// ---------------------------------------------------------------------------

function runClustering() {
    fetch("/api/topics/cluster", { method: "POST" })
        .then(function(r) { return r.json(); })
        .then(function(data) {
            if (data.topics) {
                window.location.reload();
            }
        })
        .catch(function(err) { console.error("Clustering error:", err); });
}

// ---------------------------------------------------------------------------
// Utilities
// ---------------------------------------------------------------------------

function escapeHtml(str) {
    if (!str) return "";
    var div = document.createElement("div");
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
}

function formatTime(isoStr) {
    if (!isoStr) return "";
    try {
        var d = new Date(isoStr);
        return d.toLocaleTimeString();
    } catch (e) {
        return isoStr;
    }
}

function setTextIfExists(id, value) {
    var el = document.getElementById(id);
    if (el) el.textContent = value;
}

// ---------------------------------------------------------------------------
// Init
// ---------------------------------------------------------------------------

document.addEventListener("DOMContentLoaded", function() {
    // Draw gauge on dashboard
    var gaugeScore = document.getElementById("gauge-score");
    if (gaugeScore) {
        drawGauge("sentiment-gauge", parseFloat(gaugeScore.textContent) || 0);
    }

    // Char counter for analyze page
    var analyzeInput = document.getElementById("analyze-input");
    if (analyzeInput) {
        analyzeInput.addEventListener("input", updateCharCount);
    }
});
