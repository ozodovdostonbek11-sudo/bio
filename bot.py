import asyncio
import random
import os
from telethon import TelegramClient, events, functions
from telethon.errors import FloodWaitError

api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
bot_token = os.getenv("BOT_TOKEN")

client = TelegramClient("bot", api_id, api_hash)

@client.on(events.NewMessage)
async def handler(event):
    text = event.raw_text
    usernames = [u.replace("@", "").strip() for u in text.split() if u.strip()]

    empty, busy = [], []

    for username in usernames:
        try:
            result = await client(functions.account.CheckUsernameRequest(username))

            if result:
                empty.append(username)
            else:
                busy.append(username)

            await asyncio.sleep(random.randint(4, 8))

        except FloodWaitError as e:
            await asyncio.sleep(e.seconds)

        except:
            continue

    msg = ""

    if empty:
        msg += "✅ Available:\n" + "\n".join(empty) + "\n\n"

    if busy:
        msg += "❌ Taken:\n" + "\n".join(busy)

    await event.reply(msg or "No valid usernames")

async def main():
    print("Bot running...")
    await client.start(bot_token=bot_token)
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
