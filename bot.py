import asyncio
import random
import os
from telethon import TelegramClient, events, functions
from telethon.errors import FloodWaitError

api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
bot_token = os.getenv("BOT_TOKEN")

client = TelegramClient("bot", api_id, api_hash).start(bot_token=bot_token)

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

        except Exception:
            continue

    msg = ""

    if empty:
        msg += "✅ Available:\n" + "\n".join(empty) + "\n\n"

    if busy:
        msg += "❌ Taken:\n" + "\n".join(busy)

    await event.reply(msg or "No valid usernames")

# 🔥 Anti-crash loop
async def main():
    while True:
        try:
            print("Bot started...")
            await client.run_until_disconnected()
        except Exception as e:
            print(f"Restarting... {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
    
