import asyncio
import random
from telethon import TelegramClient, events, functions
from telethon.errors import FloodWaitError
import os

api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
bot_token = os.getenv("BOT_TOKEN")

client = TelegramClient("bot", api_id, api_hash).start(bot_token=bot_token)

@client.on(events.NewMessage)
async def handler(event):
    text = event.raw_text

    usernames = [u.replace("@", "").strip() for u in text.split() if u.strip()]

    empty = []
    busy = []

    for username in usernames:
        try:
            result = await client(functions.account.CheckUsernameRequest(username))

            if result:
                empty.append(username)
            else:
                busy.append(username)

            await asyncio.sleep(random.randint(5, 10))

        except FloodWaitError as e:
            await asyncio.sleep(e.seconds)

        except:
            pass

    msg = ""

    if empty:
        msg += "✅ Available:\n" + "\n".join(empty) + "\n\n"

    if busy:
        msg += "❌ Taken:\n" + "\n".join(busy)

    await event.reply(msg if msg else "No valid usernames")

async def main():
    await client.run_until_disconnected()

asyncio.run(main())
