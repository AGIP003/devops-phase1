## Local Setup

1. Clone the repo
2. cd project2 && python3 -m venv venv && source venv/bin/activate
3. pip install -r requirements.txt
4. cp .env.example .env — fill in values (see comments in file)
5. cd ../tracker-frontend && npm install
6. Run backend: flask run (port 5000)
7. Run frontend: npm run dev (port 5173)
8. Run bot: python -m bot.main