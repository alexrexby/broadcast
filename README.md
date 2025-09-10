# Broadcast — Telegram Content-Delivery Bot

This project is a backend service and Telegram bot designed for daily and manual broadcasts of themes or content, delivering value only to subscribers of your Telegram channel(s). The admin panel and REST API make it easy to manage users, content, send messages, and track delivery statistics.

---

## 🚀 Features

- Daily topic/message auto-broadcast for all subscribers
- One-off/manual mass messaging by admin
- Subscription check: only users subscribed to the required channel(s) receive content
- Web admin panel for:
  - Managing users (view, filter by subscription, history)
  - Content plan editor (add/edit/delete topics)
  - Manual broadcast sender
  - Updatable bot token & list of required channels
  - Viewing message delivery history and stats
- REST API for integration with other systems

---

## 📦 Project structure

core/ # Business logic: services for users, themes, broadcasts
db/ # Database models and migration scripts (SQLAlchemy)
bot/ # Telegram bot handlers and utilities
api/ # REST API endpoints (FastAPI)
config/ # .env and other config files
tests/ # Unit and integration tests
requirements.txt
README.md


---

## 🛠️ Getting started

1. **Clone the repository**
    ```
    git clone https://github.com/alexrexby/broadcast.git
    cd broadcast
    ```
2. **Install dependencies**
    ```
    pip install -r requirements.txt
    ```
3. **Edit environment variables**
    - Copy and rename `.env.example` to `.env`.  
    - Fill in your own values (`BOT_TOKEN`, database settings, etc).

4. **Initialize the database**
    ```
    python db/init_db.py
    ```

5. **Run the API and the bot**
    ```
    python api/main.py          # Starts the web API/admin
    python bot/app.py           # Starts the Telegram bot
    ```

---

## ⚙️ .env Example

BOT_TOKEN=123456789:ABC-DEFyourbot_token
ADMIN_PASSWORD=changeme
REQUIRED_CHANNELS=-100123456789,@example_channel
DATABASE_URL=sqlite:///./project.db


---

## ✅ Roadmap

- [x] Basic folder structure
- [ ] Core services (users, themes, broadcasts)
- [ ] DB models & migrations
- [ ] Telegram bot logic
- [ ] Admin web panel
- [ ] API documentation (Swagger)
- [ ] Tests

---

## 🙌 Contributions

Your ideas, bugfixes, and PRs are welcome!
Open issues or propose features via GitHub Issues.

---

## © License

MIT (fill in as needed)
