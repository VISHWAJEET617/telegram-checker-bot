# 🤖 Telegram Premium Checker Bot

Complete production-ready Telegram bot for checking premium accounts and managing user credits.

## ✨ Features

- 🎉 **Premium Home Screen** - Beautiful 4-button home interface
- 👤 **User Profiles** - Track user stats and credits
- 💳 **Card Checking** - Single and mass card verification
- 🧪 **Multiple Gates** - Razorpay, Stripe, Auth payment gateways
- 💎 **Tiered Plans** - Free, Premium, and Diamond tiers
- 📊 **Statistics** - Track checks, results, and spending
- 💾 **SQLite Database** - Persistent user data storage
- 📁 **File Upload** - Support for .txt file batch processing
- ⚡ **Error Handling** - Robust error management
- 🔐 **Security** - Luhn algorithm card validation

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- pip (Python package manager)
- Telegram account
- Bot token from @BotFather

### Installation

1. **Clone/Extract the repository:**
```bash
unzip telegram-checker-bot.zip
cd telegram-checker-bot
```

2. **Create virtual environment (optional but recommended):**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Setup configuration:**
```bash
cp .env.example .env
```

5. **Edit `.env` file with your settings:**
```
BOT_TOKEN=YOUR_BOT_TOKEN_FROM_BOTFATHER
ADMIN_ID=YOUR_TELEGRAM_USER_ID
OWNER_NAME=Your Name
DEVELOPER_NAME=Your Name
```

6. **Run the bot:**
```bash
python main.py
```

## 🔧 Getting Your Bot Token

1. Open Telegram
2. Search for **@BotFather**
3. Send `/newbot`
4. Follow the instructions
5. Copy your bot token (looks like: `123456:ABC-DEF...`)
6. Paste it in `.env` file as `BOT_TOKEN`

## 📝 Commands

### Main Commands
- `/start` - Show home menu
- `/help` - Display help message
- `/cmds` - List all commands
- `/profile` - Show your profile
- `/stats` - Display statistics

### Checking Commands
- `/rz CARD|MM|YY|CVV` - Check single card
- `/mrz` - Start mass check mode

### Admin Commands
- `/stats` - Bot statistics
- `/users` - Total users count

## 💳 Card Format

Cards must be in the format: `CARD|MM|YY|CVV`

**Example:**
```
4111111111111111|12|25|123
```

Where:
- `CARD` = Card number (13-19 digits)
- `MM` = Month (01-12)
- `YY` = Year (2 digits, e.g., 25 for 2025)
- `CVV` = Security code (3-4 digits)

## 📊 Database

The bot uses SQLite database stored in `data/checker.db` with tables:
- `users` - User information and credits
- `transactions` - Credit transactions history
- `checks` - Card check history

## 🎪 Plans

### Free Plan
- **Credits:** 25
- **Single Check:** ✅
- **Mass Check:** ❌

### Premium Plan
- **Credits:** 5,000
- **Single Check:** ✅
- **Mass Check:** ✅ (100 cards/check)

### Diamond Plan
- **Credits:** Unlimited
- **Single Check:** ✅
- **Mass Check:** ✅ (1,000 cards/check)

## 🧪 Payment Gates

- **Razorpay** - Indian payment gateway (Ready)
- **Stripe** - Global payment gateway (Coming Soon)
- **Auth Gate** - Custom authentication (Coming Soon)

## 📂 Project Structure

```
telegram-checker-bot/
├── main.py                 # Bot entry point
├── db.py                   # Database module
├── utils.py                # Utility functions
├── keyboards.py            # UI keyboards
├── handlers/               # Command handlers
│   ├── __init__.py
│   ├── start.py
│   ├── commands.py
│   ├── single_check.py
│   ├── mass_check.py
│   └── navigation.py
├── gates/                  # Payment gateways
│   ├── __init__.py
│   └── razorpay.py
├── .env.example            # Config template
├── requirements.txt        # Python dependencies
├── Dockerfile              # Docker configuration
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## 🐳 Docker Deployment

### Build Docker image:
```bash
docker build -t telegram-checker-bot .
```

### Run container:
```bash
docker run -e BOT_TOKEN=YOUR_TOKEN -v $(pwd)/data:/app/data telegram-checker-bot
```

## 🔒 Security Features

- **Luhn Algorithm** - Validates card numbers
- **Input Validation** - Validates all user inputs
- **Credit System** - Prevents unauthorized usage
- **Admin Control** - Owner/admin management
- **Error Handling** - Graceful error recovery

## 📈 Scalability

- Supports unlimited users
- Efficient SQLite database
- Async/await for concurrent requests
- Stateless design for horizontal scaling

## 🔐 Privacy

- No card data stored (only last 4 digits logged)
- User data encrypted in database
- Secure token management
- GDPR compliant

## 🐛 Troubleshooting

### Bot not responding?
- Check if bot is running
- Verify BOT_TOKEN is correct
- Check for errors in logs

### Commands not working?
- Make sure bot is running
- Use correct command format
- Check user permissions

### Database errors?
- Delete `data/checker.db`
- Bot will auto-create on next run
- Check folder permissions

## 📞 Support

For issues, feature requests, or contributions:
1. Check existing issues
2. Open a new issue with details
3. Include error logs if applicable

## 📄 License

MIT License - See LICENSE file for details

## 👨‍💻 Author

**Developer:** Your Name  
**Owner:** Your Name  
**Created:** 2026

## 🙏 Acknowledgments

- Aiogram library
- Python community
- Telegram bot API

---

**Ready to check! Start the bot and send `/start` 🚀**

