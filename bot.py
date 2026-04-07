import asyncio
import logging
import os
import re

from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.functions.contacts import ResolveUsernameRequest
from telethon.tl.functions.account import UpdateUsernameRequest
from telethon.errors import (
    UsernameNotOccupiedError,
    UsernameOccupiedError,
    FloodWaitError
)

# -------- CONFIG --------
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PRO")

# -------- PARSER --------
def extract_usernames(text):
    return list(set(re.findall(r'@?([a-zA-Z0-9_]{5,32})', text)))

# -------- FAST CHECK --------
async def fast_check(username):
    try:
        await client(ResolveUsernameRequest(username))
        return False  # band
    except UsernameNotOccupiedError:
        return True   # ehtimol bo‘sh
    except:
        return False

# -------- REAL CHECK --------
async def real_check(username, original):
    try:
        await client(UpdateUsernameRequest(username))
        await client(UpdateUsernameRequest(original))  # qaytarish
        return True
    except UsernameOccupiedError:
        return False
    except FloodWaitError as e:
        await asyncio.sleep(e.seconds)
        return await real_check(username, original)
    except:
        return False

# -------- MAIN CHECK --------
async def check_usernames(usernames):
    me = await client.get_me()
    original = me.username

    real_available = []

    for username in usernames:
        is_free = await fast_check(username)

        if not is_free:
            continue

        # REAL check
        ok = await real_check(username, original)

        if ok:
            real_available.append(username)

        await asyncio.sleep(2)

    return real_available

# -------- HANDLER --------
@client.on(events.NewMessage(incoming=True))
async def handler(event):
    if OWNER_ID and event.sender_id != OWNER_ID:
        return

    usernames = extract_usernames(event.raw_text)

    if not usernames:
        await event.reply("❌ No valid usernames")
        return

    msg = await event.reply("🔍 Checking REAL availability...")

    result = await check_usernames(usernames)

    if result:
        text = "🔥 REAL AVAILABLE:\n" + "\n".join(f"@{u}" for u in result)
    else:
        text = "❌ No real available usernames"

    await msg.edit(text)

# -------- MAIN --------
async def main():
    await client.start()
    me = await client.get_me()

    logger.info(f"Connected as {me.first_name}")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
