# Sameer's Buy Buddy 🛒💻

A minimal gaming laptop price tracker built with **Flask + Playwright** that compares laptop prices across multiple Indian e-commerce platforms in real time.

Track prices from:
- Amazon India
- Flipkart
- Reliance Digital
- Croma

---

## ✨ Features

- 🔍 Search gaming laptops instantly
- 📊 Compare prices across stores
- 📈 Price history tracking using SQLite
- 🤖 Smart "Best Time to Buy" recommendation
- 🎨 Minimal comic-style UI
- ⚡ Fast Playwright-based scraping
- 🕶️ Stealth scraping setup to reduce blocking

---

## 🛠️ Tech Stack

### Frontend
- HTML
- CSS
- JavaScript
- Chart.js

### Backend
- Python
- Flask
- Playwright

### Database
- SQLite

---

## 📂 Project Structure

```bash
sameers-buy-buddy/
│
├── scrapers/
│   ├── amazon.py
│   ├── flipkart.py
│   ├── reliance.py
│   ├── croma.py
│   └── __init__.py
│
├── static/
│   ├── style.css
│   ├── script.js
│   └── chart.js
│
├── templates/
│   └── index.html
│
├── app.py
├── requirements.txt
├── database.db
└── README.md# sameers-buy-buddy
