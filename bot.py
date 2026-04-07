import asyncio
import random
import os
import re
from telethon import TelegramClient, events, functions
from telethon.errors import FloodWaitError

# 🔑 ENV (Railway’dan olinadi)
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
bot_token = os.getenv("BOT_TOKEN")

# 🔌 Client
client = TelegramClient("bot", api_id, api_hash)

# 🤖 Message handler
@client.on(events.NewMessage)
async def handler(event):
    text = event.raw_text

    # 🔍 Username ajratish (har qanday formatdan)
    usernames = re.findall(r'@?([a-zA-Z0-9_]{5,32})', text)

    if not usernames:
        await event.reply("❌ No valid usernames found")
        return

    empty = []
    busy = []

    for username in usernames:
        try:
            result = await client(functions.account.CheckUsernameRequest(username))

            if result:
                empty.append(username)
            else:
                busy.append(username)

            # ⏱ Anti-flood delay
            await asyncio.sleep(random.randint(4, 8))

        except FloodWaitError as e:
            await asyncio.sleep(e.seconds)

        except Exception:
            continue

    # 📊 Natija
    msg = ""

    if empty:
        msg += "✅ Available:\n" + "\n".join(empty) + "\n\n"

    if busy:
        msg += "❌ Taken:\n" + "\n".join(busy)

    await event.reply(msg or "No valid usernames")

# ▶️ Run
async def main():
    print("🚀 Bot running...")
    await client.start(bot_token=bot_token)
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
