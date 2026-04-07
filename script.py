import asyncio
import random
from datetime import datetime
from telethon import TelegramClient, functions
from telethon.errors import FloodWaitError

api_id = 123456
api_hash = 'API_HASH'

DAILY_LIMIT = 20

client = TelegramClient('session', api_id, api_hash)

created_today = 0
base_delay = 8  # boshlang'ich delay

def log(text):
    t = datetime.now().strftime("%H:%M:%S")
    print(f"[{t}] {text}")

async def main():
    global created_today, base_delay

    await client.start()

    with open("usernames.txt") as f:
        usernames = [u.strip() for u in f if u.strip()]

    for i, username in enumerate(usernames, 1):

        if created_today >= DAILY_LIMIT:
            log("🚫 Kunlik limitga yetdi")
            break

        try:
            log(f"Tekshirilmoqda: {username}")

            result = await client(functions.account.CheckUsernameRequest(username))

            if result:
                log(f"Bo'sh: {username}")

                ch = await client(functions.channels.CreateChannelRequest(
                    title=username,
                    about="Auto",
                    megagroup=False
                ))

                channel = ch.chats[0]

                await client(functions.channels.UpdateUsernameRequest(
                    channel=channel,
                    username=username
                ))

                created_today += 1
                log(f"✅ Ochildi ({created_today}/{DAILY_LIMIT})")

            else:
                log("Band")

            # 🧠 Smart delay
            delay = random.randint(base_delay, base_delay + 10)
            log(f"Kutish: {delay}s")
            await asyncio.sleep(delay)

            # 🔄 Har 5 ta urinishdan keyin dam
            if i % 5 == 0:
                rest = random.randint(40, 90)
                log(f"☕ Dam: {rest}s")
                await asyncio.sleep(rest)

        except FloodWaitError as e:
            log(f"⛔ Flood: {e.seconds}s")

            # 🧠 Delayni oshiramiz
            base_delay += 3
            log(f"Yangi delay: {base_delay}")

            await asyncio.sleep(e.seconds + 5)

        except Exception as e:
            log(f"Xatolik: {e}")
            await asyncio.sleep(5)

asyncio.run(main())
