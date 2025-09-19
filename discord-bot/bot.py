import os, time, json, threading, requests, asyncio, aiohttp, sys
from discord import Intents
from discord.ext import commands

DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')
BACKEND_SSE = os.environ.get('BACKEND_SSE','http://investorsentinel-backend:8000/api/stream/sse/')
BACKEND_API = os.environ.get('BACKEND_API','http://investorsentinel-backend:8000')
BOT_PREFIX = os.environ.get('BOT_PREFIX','!')

intents = Intents.default()
bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents)

async def post_to_channel(bot, channel_id, message):
    try:
        ch = bot.get_channel(int(channel_id))
        if ch:
            await ch.send(message)
        else:
            print('Channel not found in cache', channel_id)
    except Exception as e:
        print('post error', e)

async def sse_listener():
    await bot.wait_until_ready()
    session = aiohttp.ClientSession()
    try:
        async with session.get(BACKEND_SSE) as resp:
            if resp.status != 200:
                print('SSE endpoint responded', resp.status)
                await session.close()
                return
            print('Connected to SSE')
            async for line in resp.content:
                try:
                    s = line.decode().strip()
                    if not s: continue
                    if s.startswith('data:'):
                        payload = s[len('data:'):].strip()
                        data = json.loads(payload)
                        ticker = data.get('ticker')
                        # fetch subscriptions for this ticker
                        try:
                            subs = requests.get(BACKEND_API + '/api/subscriptions/').json()
                        except Exception:
                            subs = []
                        message = f"**ALERT**: {ticker} score={data.get('score')}\n{data.get('summary','')[:800]}"
                        for sub in subs:
                            # simple mapping: if sub.company matches ticker then notify channels
                            try:
                                # in this starter, subscriptions list contains all subs; fetch company per sub is omitted for simplicity
                                chan = sub.get('discord_channel')
                                if chan:
                                    await post_to_channel(bot, chan, message)
                                # Slack via webhook on backend delivery; backend deliver_alert handles Slack/Jira
                            except Exception as e:
                                print('forward error', e)
                except Exception as e:
                    print('sse parse error', e)
    except Exception as e:
        print('sse connection error', e)
    finally:
        await session.close()

@bot.event
async def on_ready():
    print(f'Bot ready: {bot.user}')

@bot.command()
async def subscribe(ctx, ticker: str):
    api = BACKEND_API + '/api/subscriptions/add/'
    payload = {'ticker': ticker, 'channel': str(ctx.channel.id)}
    try:
        r = requests.post(api, json=payload)
        if r.status_code == 200:
            await ctx.send(f'Subscribed this channel to {ticker.upper()} alerts.')
        else:
            await ctx.send(f'Error subscribing: {r.text}')
    except Exception as e:
        await ctx.send('Error contacting backend.')

@bot.command()
async def subscribe_slack(ctx, ticker: str, slack_channel: str, jira_project: str = ''):
    # create subscription that includes slack channel and jira project
    api = BACKEND_API + '/api/subscriptions/add/'
    payload = {'ticker': ticker, 'channel': str(ctx.channel.id), 'slack': slack_channel, 'jira': jira_project}
    try:
        r = requests.post(api, json=payload)
        if r.status_code == 200:
            await ctx.send(f'Subscribed to {ticker.upper()} with Slack {slack_channel} and Jira {jira_project}.')
        else:
            await ctx.send(f'Error: {r.text}')
    except Exception as e:
        await ctx.send('Error contacting backend.')

@bot.command()
async def unsub(ctx, ticker: str):
    await ctx.send('Unsubscribe not implemented in starter. Use admin to remove subscription.')

def start_background_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_until_complete(sse_listener())

if __name__ == '__main__':
    if not DISCORD_TOKEN:
        print('DISCORD_TOKEN not set')
        sys.exit(1)
    new_loop = asyncio.new_event_loop()
    t = threading.Thread(target=start_background_loop, args=(new_loop,), daemon=True)
    t.start()
    bot.run(DISCORD_TOKEN)
