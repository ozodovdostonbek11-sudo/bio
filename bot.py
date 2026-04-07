import asyncio
import logging
import os
import re
import random
from typing import Tuple, List
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError
from telethon.sessions import StringSession
from telethon.tl.functions.account import CheckUsernameRequest

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

API_ID = int(os.getenv('API_ID', '0'))
API_HASH = os.getenv('API_HASH', '')
SESSION_STRING = os.getenv('SESSION_STRING', '')
OWNER_ID = int(os.getenv('OWNER_ID', '0'))

if not all([API_ID, API_HASH, SESSION_STRING]):
    raise ValueError("Missing required environment variables: API_ID, API_HASH, SESSION_STRING")

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)


def extract_usernames(text: str) -> List[str]:
    """Extract valid usernames from messy input."""
    cleaned = re.sub(r'[^\w@\s\n]', '', text, flags=re.UNICODE)
    potential = re.findall(r'@?([a-zA-Z0-9_]+)', cleaned)
    
    valid = []
    for username in potential:
        if 5 <= len(username) <= 32 and not username.isdigit() and re.match(r'^[a-zA-Z0-9_]+$', username):
            if username not in valid:
                valid.append(username)
    
    return valid


async def check_username(username: str) -> Tuple[str, bool]:
    """Check if username is available."""
    try:
        await client(CheckUsernameRequest(username))
        return username, True
    except Exception as e:
        error_msg = str(e).lower()
        if 'occupied' in error_msg or 'taken' in error_msg:
            return username, False
        elif 'not occupied' in error_msg:
            return username, True
        elif 'flood' in error_msg:
            logger.warning(f"FloodWaitError for {username}, retrying...")
            await asyncio.sleep(5)
            return await check_username(username)
        else:
            logger.error(f"Error checking {username}: {e}")
            return username, None


async def check_usernames_batch(usernames: List[str]) -> Tuple[List[str], List[str]]:
    """Check multiple usernames with anti-flood protection."""
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
    """Format results into a clean message."""
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


@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    """Handle /start command."""
    if OWNER_ID and event.sender_id != OWNER_ID:
        await event.reply("❌ Unauthorized access.")
        return
    
    welcome = (
        "🤖 **Telegram Username Checker**\n\n"
        "Send me usernames to check availability.\n\n"
        "**Format:**\n"
        "• One per line\n"
        "• With or without @\n"
        "• 5-32 characters\n"
        "• Letters, numbers, underscores only\n\n"
        "**Example:**\n"
        "```\nusername1\n@username2\nusername_3\n```"
    )
    await event.reply(welcome, parse_mode='markdown')
    logger.info(f"Start command from {event.sender_id}")


@client.on(events.NewMessage(incoming=True))
async def check_handler(event):
    """Handle username checking requests."""
    if event.message.text.startswith('/'):
        return
    
    if OWNER_ID and event.sender_id != OWNER_ID:
        await event.reply("❌ Unauthorized access.")
        return
    
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
    """Main function to start the bot."""
    logger.info("Starting Telegram Username Checker Bot...")
    
    try:
        await client.connect()
        logger.info("User session connected successfully")
        
        me = await client.get_me()
        logger.info(f"Connected as: {me.first_name} (@{me.username})")
        
        await client.run_until_disconnected()
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
    finally:
        await client.disconnect()


if __name__ == '__main__':
    asyncio.run(main())

async def start_handler(event):
    """Handle /start command."""
    if OWNER_ID and event.sender_id != OWNER_ID:
        await event.reply("❌ Unauthorized access.")
        return
    
    welcome = (
        "🤖 **Telegram Username Checker**\n\n"
        "Send me usernames to check availability.\n\n"
        "**Format:**\n"
        "• One per line\n"
        "• With or without @\n"
        "• 5-32 characters\n"
        "• Letters, numbers, underscores only\n\n"
        "**Example:**\n"
        "```\nusername1\n@username2\nusername_3\n```"
    )
    await event.reply(welcome, parse_mode='markdown')
    logger.info(f"Start command from {event.sender_id}")


@client.on(events.NewMessage(incoming=True))
async def check_handler(event):
    """Handle username checking requests."""
    if event.message.text.startswith('/'):
        return
    
    if OWNER_ID and event.sender_id != OWNER_ID:
        await event.reply("❌ Unauthorized access.")
        return
    
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
    """Main function to start the bot."""
    logger.info("Starting Telegram Username Checker Bot...")
    
    try:
        # Import session string
        await client.import_session_string(SESSION_STRING)
        await client.connect()
        logger.info("User session connected successfully")
        
        me = await client.get_me()
        logger.info(f"Connected as: {me.first_name} (@{me.username})")
        
        await client.run_until_disconnected()
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
    finally:
        await client.disconnect()


if __name__ == '__main__':
    asyncio.run(main())
SESSION_STRING olish uchun (lokal kompyuteringizda):

get_session.py faylini yarating:

import asyncio
from telethon import TelegramClient

API_ID = int(input("API_ID: "))
API_HASH = input("API_HASH: ")
PHONE = input("PHONE (+998...): ")

async def main():
    client = TelegramClient('temp_session', API_ID, API_HASH)
    await client.start(phone=PHONE)
    
    # Get session string
    session_string = client.session.save()
    print("\n✅ SESSION_STRING:")
    print(session_string)
    
    await client.disconnect()

asyncio.run(main())
