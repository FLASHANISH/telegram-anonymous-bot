from flask import Flask
from threading import Thread
import time

app = Flask(__name__)

@app.route('/')
def home():
    return """
    <html>
    <head><title>Telegram Bot Status</title></head>
    <body style="font-family: Arial; text-align: center; padding: 50px;">
        <h1>🤖 Anonymous Telegram Bot</h1>
        <h2 style="color: green;">✅ Bot is Running!</h2>
        <p>Your bot is live and processing messages 24/7</p>
        <p><strong>Repository:</strong> <a href="https://github.com/FLASHANISH/telegram-anonymous-bot">GitHub</a></p>
    </body>
    </html>
    """

@app.route('/status')
def status():
    return {"status": "online", "message": "Bot is running successfully"}

def run():
    app.run(host='0.0.0.0', port=8080, debug=False)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()
