## Local Setup

1. Clone the repo
2. cd project2 && python3 -m venv venv && source venv/bin/activate
3. pip install -r requirements.txt
4. cp .env.example .env — fill in values (see comments in file)
5. cd ../tracker-frontend && npm install
6. Run backend: flask run (port 5000)
7. Run frontend: npm run dev (port 5173)
8. Run bot: python -m bot.main

## Logs

The backend and Telegram bot log to the terminal or hosting platform process logs.

- Backend API: check the terminal running `flask run` or the hosted `web` process.
- Telegram bot: check the terminal running `python -m bot.main` or the hosted `worker` process.
- Slow API requests are logged with `duration_ms`; requests slower than `SLOW_REQUEST_MS` are warnings.

Useful local commands:

```bash
cd project2
LOG_LEVEL=INFO SLOW_REQUEST_MS=500 flask run
LOG_LEVEL=INFO python3 -m bot.main
```
