import os, time, json, threading, requests
import asyncio
import aiohttp
import sys
from discord import Intents
from discord.ext import commands

DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')
BACKEND_SSE = os.environ.get('BACKEND_SSE','http://investorsentinel-backend:8000/api/stream/sse/')
BOT_PREFIX = os.environ.get('BOT_PREFIX','!')

intents = Intents.default()
bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents)

# helper: post message to channel id (string)
async def post_to_channel(bot, channel_id, message):
    try:
        ch = bot.get_channel(int(channel_id))
        if ch:
            await ch.send(message)
        else:
            print('Channel not found in cache', channel_id)
    except Exception as e:
        print('post error', e)

# Background task: connect to SSE and forward alerts
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
                        # fetch subscriptions for ticker via REST API
                        try:
                            subs = requests.get(os.environ.get('BACKEND_API','http://investorsentinel-backend:8000') + '/api/subscriptions/').json()
                        except Exception:
                            subs = []
                        # send to subscribed channels that match ticker
                        for sub in subs:
                            # simple: check subscription's company ticker by fetching company
                            try:
                                # get company for subscription
                                # This is simplified; in production, map subscription to company
                                if True:
                                    # forward message to channel id stored in subscription
                                    chan = sub.get('discord_channel')
                                    msg = f"ALERT: {data.get('ticker')} score={data.get('score')} summary={data.get('summary')[:200]}")
                                    await post_to_channel(bot, chan, msg)
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

# simple commands to manage subscriptions
@bot.command()
async def subscribe(ctx, ticker: str):
    # store subscription: use backend API
    api = os.environ.get('BACKEND_API','http://investorsentinel-backend:8000') + '/api/subscriptions/add/'
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
async def unsub(ctx, ticker: str):
    # Note: backend doesn't have unsubscribe in starter; inform user
    await ctx.send('Unsubscribe not implemented in starter. Use admin to remove subscription.')

def start_background_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_until_complete(sse_listener())

if __name__ == '__main__':
    if not DISCORD_TOKEN:
        print('DISCORD_TOKEN not set')
        sys.exit(1)
    # run sse listener in background thread using asyncio loop
    new_loop = asyncio.new_event_loop()
    t = threading.Thread(target=start_background_loop, args=(new_loop,), daemon=True)
    t.start()
    bot.run(DISCORD_TOKEN)
