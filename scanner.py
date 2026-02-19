import requests
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

print("Testing Telegram...")

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
r = requests.post(url, data={
    "chat_id": CHAT_ID,
    "text": "🚀 Fly bot test message"
})

print("Response:", r.text)
