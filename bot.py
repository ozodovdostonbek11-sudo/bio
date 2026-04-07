import asyncio
import logging
import os
import re
import random
from typing import Tuple, List
from telethon import TelegramClient, events
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
    cleaned = re.sub(r'[^\w@\s\n]', '', text, flags=re.UNICODE)
    potential = re.findall(r'@?([a-zA-Z0-9_]+)', cleaned)
    
    valid = []
    for username in potential:
        if 5 <= len(username) <= 32 and not username.isdigit() and re.match(r'^[a-zA-Z0-9_]+$', username):
            if username not in valid:
                valid.append(username)
    
    return valid


async def main():
    logger.info("Starting Telegram Username Checker Bot...")
    
    try:
        await client.connect()
        logger.info("User session connected successfully")
        
        me = await client.get_me()
        logger.info(f"Connected as: {me.first_name} (@{me.username})")
        
        logger.info("Bot is running and listening for messages...")
        
        # Keep bot running
        while True:
            await asyncio.sleep(1)
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
    finally:
        await client.disconnect()
    
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
        return "No valid usernames found. Use 


if __name__ == '__main__':
    asyncio.run(main())
