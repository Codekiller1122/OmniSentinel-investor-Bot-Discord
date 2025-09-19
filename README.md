# OmniSentinel - Cross-platform Alert Bot (Discord, Slack, Jira)

OmniSentinel forwards AI-driven stock sentiment alerts to Discord, Slack, and Jira.

## Components
- `backend/` (Django): alert ingestion, SSE stream, delivers Slack messages and creates Jira issues when subscriptions specify those channels/projects.
- `discord-bot/`: Discord bot that listens to SSE and posts alerts to subscribed channels. Offers `!subscribe TICKER` and `!subscribe_slack TICKER SLACK_CHANNEL [JIRA_PROJECT]`.

## Quickstart (Docker)
1. Fill `backend/.env.example` and `discord-bot/.env.example` with real values.
2. Build and run:
   ```bash
   docker-compose up --build
   ```
3. In backend container:
   ```bash
   docker exec -it $(docker ps -qf "ancestor=omnisentinel-backend") python manage.py migrate
   docker exec -it $(docker ps -qf "ancestor=omnisentinel-backend") python manage.py seed_companies
   ```
4. Invite the Discord bot and set `DISCORD_TOKEN`.

## How alerts flow
- External scanner posts to `/api/alerts/create/` with `ticker`, `score`, and `summary`.
- Backend stores Alert and delivers Slack/Jira based on subscriptions, and exposes SSE stream for real-time forwarding to the Discord bot.

## Notes
- Slack: backend posts to a single `SLACK_WEBHOOK_URL` by default or per-subscription override via `slack_channel` (you may set channel-specific webhooks).
- Jira: backend creates an issue in the subscription's `jira_project` if Jira env vars are configured.
- This is a starter: implement auth, retry/backoff, and secure webhooks for production.
