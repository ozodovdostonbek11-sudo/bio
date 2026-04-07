import asyncio
import logging
import os
import re
from typing import List

from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.functions.contacts import ResolveUsernameRequest
from telethon.errors import UsernameNotOccupiedError, FloodWaitError

# ---------------- LOGGING ----------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("checker")

# ---------------- ENV ----------------
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
SESSION_STRING = os.getenv("SESSION_STRING", "")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))  # optional

if not all([API_ID, API_HASH, SESSION_STRING]):
    raise ValueError("API_ID, API_HASH, SESSION_STRING required")

# ---------------- CLIENT ----------------
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# ---------------- USERNAME PARSER ----------------
def extract_usernames(text: str) -> List[str]:
    usernames = re.findall(r'@?([a-zA-Z0-9_]{5,32})', text)
    return list(set(usernames))

# ---------------- CHECK FUNCTION ----------------
async def check_username(username: str):
    try:
        await client(ResolveUsernameRequest(username))
        return "taken"
    except UsernameNotOccupiedError:
        return "available"
    except FloodWaitError as e:
        logger.warning(f"FloodWait {e.seconds}s")
        await asyncio.sleep(e.seconds)
        return await check_username(username)
    except Exception as e:
        logger.error(f"{username} error: {e}")
        return "error"

# ---------------- FORMAT ----------------
def format_result(available, taken, errors):
    text = ""

    if available:
        text += "✅ Available:\n"
        text += "\n".join(f"@{u}" for u in available)

    if taken:
        if text:
            text += "\n\n"
        text += "❌ Taken:\n"
        text += "\n".join(f"@{u}" for u in taken)

    if errors:
        if text:
            text += "\n\n"
        text += "⚠️ Errors:\n"
        text += "\n".join(f"@{u}" for u in errors)

    if not text:
        return "❗ No valid usernames found."

    return text

# ---------------- HANDLER ----------------
@client.on(events.NewMessage)
async def handler(event):
    # OWNER filter (optional)
    if OWNER_ID and event.sender_id != OWNER_ID:
        return

    text = event.raw_text
    usernames = extract_usernames(text)

    if not usernames:
        await event.reply("❗ No valid usernames found.")
        return

    available, taken, errors = [], [], []

    for username in usernames:
        status = await check_username(username)

        if status == "available":
            available.append(username)
        elif status == "taken":
            taken.append(username)
        else:
            errors.append(username)

        await asyncio.sleep(1.5)  # anti-flood

    result = format_result(available, taken, errors)
    await event.reply(result)

# ---------------- MAIN ----------------
async def main():
    logger.info("Starting Username Checker...")

    await client.start()

    me = await client.get_me()
    name = me.first_name or "NoName"
    username = f"@{me.username}" if me.username else "NoUsername"

    logger.info(f"Connected as: {name} ({username})")
    logger.info("Bot is running...")

    await client.run_until_disconnected()

# ---------------- RUN ----------------
if __name__ == "__main__":
    asyncio.run(main())
