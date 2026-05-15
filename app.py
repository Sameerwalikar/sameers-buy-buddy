"""
Sameer's Buy Buddy - Flask backend.

Endpoints:
  GET  /                   -> renders the single-page UI
  POST /api/search         -> { "query": "..." } scrapes all stores, stores prices,
                              returns results + history + recommendation
"""
import asyncio
import sqlite3
import statistics
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from scrapers import amazon, flipkart, reliance, croma

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "database.db"

app = Flask(__name__)


# ---------- Database helpers ----------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables on first run."""
    with get_db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS laptops (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                laptop_id INTEGER NOT NULL,
                source TEXT NOT NULL,        -- amazon / flipkart / reliance / croma
                title TEXT,
                price REAL,                  -- numeric, NULL if unavailable
                link TEXT,
                available INTEGER DEFAULT 1, -- 1/0
                checked_at TEXT NOT NULL,
                FOREIGN KEY (laptop_id) REFERENCES laptops(id)
            );
            """
        )


def upsert_laptop(query: str) -> int:
    with get_db() as conn:
        cur = conn.execute("SELECT id FROM laptops WHERE query = ?", (query,))
        row = cur.fetchone()
        if row:
            return row["id"]
        cur = conn.execute(
            "INSERT INTO laptops (query, created_at) VALUES (?, ?)",
            (query, datetime.utcnow().isoformat()),
        )
        return cur.lastrowid


def save_prices(laptop_id: int, results: list[dict]):
    now = datetime.utcnow().isoformat()
    with get_db() as conn:
        for r in results:
            conn.execute(
                """INSERT INTO prices
                   (laptop_id, source, title, price, link, available, checked_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    laptop_id,
                    r["source"],
                    r.get("title"),
                    r.get("price"),
                    r.get("link"),
                    1 if r.get("available") else 0,
                    now,
                ),
            )


def get_history(laptop_id: int):
    """Return aggregated min-price-per-day across stores for charting."""
    with get_db() as conn:
        cur = conn.execute(
            """SELECT substr(checked_at, 1, 10) AS day,
                      MIN(price) AS price
               FROM prices
               WHERE laptop_id = ? AND price IS NOT NULL
               GROUP BY day
               ORDER BY day ASC""",
            (laptop_id,),
        )
        return [{"day": r["day"], "price": r["price"]} for r in cur.fetchall()]


# ---------- Recommendation ----------
def build_recommendation(history: list[dict], current_min: float | None) -> str:
    if current_min is None:
        return "No live prices found. Try again later or refine your search."
    prices = [h["price"] for h in history if h["price"]]
    if len(prices) < 3:
        return "Not enough history yet — check back over the next few days to spot a trend."
    avg = statistics.mean(prices)
    if current_min < avg * 0.97:
        return "Price is currently lower than average. Good time to buy. 🎯"
    if current_min > avg * 1.03:
        return "Price is above average right now. Consider waiting for a sale. ⏳"
    return "Prices are around the usual range. Prices may drop during upcoming sales. 🛍️"


# ---------- Scraping orchestration ----------
async def scrape_all(query: str) -> list[dict]:
    """Run all 4 scrapers concurrently and tolerate failures."""
    tasks = [
        amazon.scrape(query),
        flipkart.scrape(query),
        reliance.scrape(query),
        croma.scrape(query),
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    cleaned = []
    for r in results:
        if isinstance(r, Exception):
            # Keep a placeholder so the UI shows the source still
            cleaned.append({
                "source": "unknown",
                "title": None,
                "price": None,
                "link": None,
                "available": False,
                "error": str(r),
            })
        else:
            cleaned.append(r)
    return cleaned


# ---------- Routes ----------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/search", methods=["POST"])
def api_search():
    payload = request.get_json(silent=True) or {}
    query = (payload.get("query") or "").strip()
    if not query:
        return jsonify({"error": "Query is required"}), 400

    try:
        results = asyncio.run(scrape_all(query))
    except Exception as e:
        return jsonify({"error": f"Scraping failed: {e}"}), 500

    laptop_id = upsert_laptop(query)
    save_prices(laptop_id, results)

    history = get_history(laptop_id)
    live_prices = [r["price"] for r in results if r.get("price")]
    current_min = min(live_prices) if live_prices else None
    recommendation = build_recommendation(history, current_min)

    return jsonify({
        "query": query,
        "results": results,
        "history": history,
        "recommendation": recommendation,
    })


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
