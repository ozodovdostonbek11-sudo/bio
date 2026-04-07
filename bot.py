import asyncio
import logging
import os
import re
from typing import List

from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.functions.contacts import ResolveUsernameRequest
from telethon.errors import UsernameNotOccupiedError, FloodWaitError

# ---------- LOG ----------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fast-checker")

# ---------- ENV ----------
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
SESSION_STRING = os.getenv("SESSION_STRING", "")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# ---------- PARSER ----------
def extract_usernames(text: str) -> List[str]:
    return list(set(re.findall(r'@?([a-zA-Z0-9_]{5,32})', text)))

# ---------- CHECK ----------
async def check_one(username: str):
    try:
        await client(ResolveUsernameRequest(username))
        return username, "taken"

    except UsernameNotOccupiedError:
        return username, "available"

    except FloodWaitError as e:
        logger.warning(f"FloodWait {e.seconds}s")
        await asyncio.sleep(e.seconds)
        return await check_one(username)

    except Exception as e:
        logger.error(f"{username} error: {e}")
        return username, "error"

# ---------- PARALLEL CHECK ----------
async def check_usernames(usernames: List[str]):
    tasks = [check_one(u) for u in usernames]
    results = await asyncio.gather(*tasks)

    available, taken, errors = [], [], []

    for username, status in results:
        if status == "available":
            available.append(username)
        elif status == "taken":
            taken.append(username)
        else:
            errors.append(username)

    return available, taken, errors

# ---------- FORMAT ----------
def format_result(a, t, e):
    text = ""

    if a:
        text += "✅ Available:\n" + "\n".join(f"@{x}" for x in a)

    if t:
        if text: text += "\n\n"
        text += "❌ Taken:\n" + "\n".join(f"@{x}" for x in t)

    if e:
        if text: text += "\n\n"
        text += "⚠️ Errors:\n" + "\n".join(f"@{x}" for x in e)

    return text or "❗ Nothing found"

# ---------- HANDLER ----------
@client.on(events.NewMessage)
async def handler(event):
    if OWNER_ID and event.sender_id != OWNER_ID:
        return

    usernames = extract_usernames(event.raw_text)

    if not usernames:
        await event.reply("❗ No valid usernames")
        return

    msg = await event.reply("⏳ Checking...")

    available, taken, errors = await check_usernames(usernames)

    result = format_result(available, taken, errors)
    await msg.edit(result)

# ---------- MAIN ----------
async def main():
    await client.start()

    me = await client.get_me()
    logger.info(f"Connected as: {me.first_name or 'NoName'}")

    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
