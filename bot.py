import asyncio
import logging
import os
import re
import random
from typing import List

from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.functions.account import CheckUsernameRequest

# ---------------- LOGGING ----------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ---------------- ENV ----------------
API_ID = int(os.getenv('API_ID', '0'))
API_HASH = os.getenv('API_HASH', '')
SESSION_STRING = os.getenv('SESSION_STRING', '')
OWNER_ID = int(os.getenv('OWNER_ID', '0'))

if not all([API_ID, API_HASH, SESSION_STRING]):
    raise ValueError("Missing required environment variables")

# ---------------- CLIENT ----------------
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# ---------------- USERNAME EXTRACTOR ----------------
def extract_usernames(text: str) -> List[str]:
    cleaned = re.sub(r'[^\w@\s\n]', '', text, flags=re.UNICODE)
    potential = re.findall(r'@?([a-zA-Z0-9_]+)', cleaned)

    valid = []
    for username in potential:
        if 5 <= len(username) <= 32 and not username.isdigit():
            if re.match(r'^[a-zA-Z0-9_]+$', username):
                if username not in valid:
                    valid.append(username)

    return valid

# ---------------- CHECK FUNCTION ----------------
async def check_username(username: str):
    try:
        result = await client(CheckUsernameRequest(username))
        return True if result else False
    except Exception:
        return False

# ---------------- FORMAT RESPONSE ----------------
def format_response(available: List[str], taken: List[str]) -> str:
    lines = []

    if available:
        lines.append("✅ Available:")
        lines.extend([f"@{u}" for u in available])

    if taken:
        if lines:
            lines.append("")
        lines.append("❌ Taken:")
        lines.extend([f"@{u}" for u in taken])

    if not lines:
        return "❗ No valid usernames found."

    return "\n".join(lines)

# ---------------- EVENT HANDLER ----------------
@client.on(events.NewMessage)
async def handler(event):
    # faqat owner ishlata oladi (ixtiyoriy)
    if OWNER_ID and event.sender_id != OWNER_ID:
        return

    text = event.raw_text
    usernames = extract_usernames(text)

    if not usernames:
        await event.reply("❗ No valid usernames found.")
        return

    available = []
    taken = []

    for username in usernames:
        try:
            is_available = await check_username(username)

            if is_available:
                available.append(username)
            else:
                taken.append(username)

            # flooddan saqlanish
            await asyncio.sleep(random.uniform(2, 4))

        except Exception as e:
            logger.error(f"Error checking {username}: {e}")

    response = format_response(available, taken)
    await event.reply(response)

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
if __name__ == '__main__':
    asyncio.run(main())
