# 🚀 Instagram Telegram Bot (Enterprise Version)

Production-ready Telegram bot for downloading Instagram posts, reels, and carousel media.

Supports:
- Videos
- Photos
- Multiple media (carousel)
- Real file size detection
- Auto delete after sending
- Queue system with workers
- Docker ready

---

## Local Run

Install dependencies:

pip install -r requirements.txt

Run:

export BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
python tbot.py

---

## Docker

Build:

docker build -t insta-bot .

Run:

docker run -d -e BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN --name insta-bot insta-bot

---

## Configuration

Inside tbot.py:

MAX_MB = 50
WORKERS = 2

Adjust based on server resources.

---

For educational use only.
