import asyncio
import logging
import os
import re
import random
from typing import Tuple, List
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import UsernameNotOccupiedError, UsernameOccupiedError

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

API_ID = int(os.getenv('API_ID', '0'))
API_HASH = os.getenv('API_HASH', '')
SESSION_STRING = os.getenv('SESSION_STRING', '')

if not all([API_ID, API_HASH, SESSION_STRING]):
    raise ValueError("Missing required environment variables: API_ID, API_HASH, SESSION_STRING")

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)


def extract_usernames(text: str) -> List[str]:
    cleaned = re.sub(r'[^\w@\s\n]', '', text, flags=re.UNICODE)
    potential = re.findall(r'@?([a-zA-Z0-9_]+)', cleaned)
    
    valid = []
    for username in potential:
        if 5 <= len(username) <= 32 and not username.isdigit() and re.match(r'^[a-zA-Z0-9_]+$', username):
            if username not in valid:
                valid.append(username)
    
    return valid


async def check_username(username: str) -> Tuple[str, bool]:
    try:
        from telethon.tl.functions.account import CheckUsernameRequest
        result = await client(CheckUsernameRequest(username))
        return username, result
    except UsernameNotOccupiedError:
        return username, True
    except UsernameOccupiedError:
        return username, False
    except Exception as e:
        error_msg = str(e).lower()
        if 'flood' in error_msg:
            logger.warning(f"FloodWaitError for {username}, retrying...")
            await asyncio.sleep(5)
            return await check_username(username)
        else:
            logger.error(f"Error checking {username}: {e}")
            return username, None


async def check_usernames_batch(usernames: List[str]) -> Tuple[List[str], List[str]]:
    available = []
    taken = []
    
    for username in usernames:
        try:
            _, is_available = await check_username(username)
            
            if is_available is True:
                available.append(username)
            elif is_available is False:
                taken.append(username)
            
            delay = random.uniform(4, 8)
            await asyncio.sleep(delay)
            
        except Exception as e:
            logger.error(f"Unexpected error with {username}: {e}")
            continue
    
    return available, taken


def format_response(available: List[str], taken: List[str]) -> str:
    lines = []
    
    if available:
        lines.append("✅ Available:")
        lines.extend(available)
    
    if taken:
        if lines:
            lines.append("")
        lines.append("❌ Taken:")
        lines.extend(taken)
    
    if not lines:
        return "No valid usernames found. Use 5-32 characters (letters, numbers, underscores)."
    
    return "\n".join(lines)


@client.on(events.NewMessage(incoming=True, pattern='/start'))
async def start_handler(event):
    welcome = (
        "🤖 **Telegram Username Checker**\n\n"
        "Send me usernames to check availability.\n\n"
        "**Format:**\n"
        "• One per line\n"
        "• With or without @\n"
        "• 5-32 characters\n"
        "• Letters, numbers, underscores only"
    )
    await event.reply(welcome, parse_mode='markdown')
    logger.info(f"Start command from {event.sender_id}")


@client.on(events.NewMessage(incoming=True, func=lambda e: e.message.text and not e.message.text.startswith('/')))
async def check_handler(event):
    try:
        text = event.message.text
        logger.info(f"Received message from {event.sender_id}: {text[:50]}...")
        
        usernames = extract_usernames(text)
        
        if not usernames:
            await event.reply("❌ No valid usernames found. Use 5-32 characters (letters, numbers, underscores).")
            return
        
        await event.reply(f"🔍 Checking {len(usernames)} username(s)...")
        
        available, taken = await check_usernames_batch(usernames)
        
        response = format_response(available, taken)
        await event.reply(response)
        
        logger.info(f"Checked {len(usernames)} usernames: {len(available)} available, {len(taken)} taken")
        
    except Exception as e:
        logger.error(f"Error in check_handler: {e}")
        await event.reply(f"❌ Error: {str(e)[:100]}")


async def main():
    logger.info("Starting Telegram Username Checker Bot...")
    
    try:
        await client.connect()
        logger.info("User session connected successfully")
        
        me = await client.get_me()
        logger.info(f"Connected as: {me.first_name} (@{me.username})")
        
        logger.info("Bot is running and listening for messages...")
        
        while True:
            await asyncio.sleep(1)
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
    finally:
        await client.disconnect()


if __name__ == '__main__':
    asyncio.run(main())
