# 🤖 Anonymous Telegram Chat Bot

A Telegram bot that enables anonymous chatting between users with multi-language support (Hindi/English).

## 🚀 Features

- **Anonymous Chat**: Connect random users for private conversations
- **Multi-language**: Support for Hindi and English
- **Content Filtering**: Blocks inappropriate links and usernames
- **Admin Controls**: Broadcast, block/unblock users, reports
- **Queue System**: Smart user matching algorithm
- **24/7 Operation**: Designed for continuous deployment

## 🛠️ Tech Stack

- **Python 3.11+**
- **python-telegram-bot** library
- **Async/Await** for high performance
- **Logging** for monitoring

## 📦 Deployment

### Deploy on Render.com

1. **Service Type**: Background Worker (NOT Web Service)
2. **Build Command**: `pip install -r requirements.txt`
3. **Start Command**: `python python.py`
4. **Environment Variable**: 
   - Key: `TELEGRAM_BOT_TOKEN`
   - Value: Your bot token from @BotFather

### Deploy on Railway/Heroku

Use the included `Procfile` and `requirements.txt`

## 🎯 Commands

- `/start` - Start the bot and join chat queue
- `/stop` - End current chat
- `/next` - Find new chat partner
- `/help` - Show all commands
- `/settings` - Change language preferences
- `/report <chat_id>` - Report inappropriate behavior

## ⚙️ Configuration

Set your bot token as environment variable:
```
TELEGRAM_BOT_TOKEN=your_token_here
```

## 🤝 Contributing

Feel free to submit issues and pull requests!

---

**⚠️ Important: This is a BACKGROUND WORKER application, not a web service!**
