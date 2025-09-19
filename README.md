# InvestorSentinel Bot - Dockerized Project

This project contains:

- `investorsentinel-backend`: Django app exposing endpoints to add companies, create alerts, and an SSE stream for realtime alerts.
- `discord-bot`: A Discord bot that connects to the backend SSE stream and posts alerts to subscribed channels. Use `!subscribe TICKER` in a channel to subscribe.

## Quickstart (local, Docker)
1. Copy environment variables into the two .env files (`investorsentinel-backend/.env.example` and `discord-bot/.env.example`) and set real values.
2. Build and run:
   ```bash
   docker-compose up --build
   ```
3. In backend container, run migrations and seed:
   ```bash
   docker exec -it $(docker ps -qf "ancestor=investorsentinel-backend") python manage.py migrate
   docker exec -it $(docker ps -qf "ancestor=investorsentinel-backend") python manage.py seed_companies
   ```
4. Invite your Discord bot to your server and set DISCORD_TOKEN in `discord-bot/.env.example`.
5. Subscribe a channel: in Discord, type `!subscribe AAPL` to subscribe the current channel to AAPL alerts.

## How it works
- External systems (e.g., Stock LeadFinder AI) POST alerts to `/api/alerts/create/` with `ticker`, `score`, and `summary`.
- Backend stores alerts and the SSE stream serves new alerts to connected listeners (the Discord bot).
- The Discord bot forwards alerts to channels recorded in `Subscription` entries.

## Notes & Next steps
- SSE listener in the bot is a simple implementation for demos. For production, use robust reconnection/backoff and authenticated SSE or WebSocket with channels mapping.
- Add unsubscribe and permission checks, and allow server admins to manage subscriptions via commands.
- Harden security: verify incoming alert sources, add auth for endpoints, and rate-limit.
