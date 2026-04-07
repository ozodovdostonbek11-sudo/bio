import asyncio
import logging
import os
import re
import random
from typing import Tuple, List
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError, UsernameNotOccupiedError, UsernameOccupiedError
from telethon.tl.functions.account import CheckUsernameRequest

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
API_ID = int(os.getenv('API_ID', '0'))
API_HASH = os.getenv('API_HASH', '')
BOT_TOKEN = os.getenv('BOT_TOKEN', '')
OWNER_ID = int(os.getenv('OWNER_ID', '0'))

# Validate credentials
if not all([API_ID, API_HASH, BOT_TOKEN]):
    raise ValueError("Missing required environment variables: API_ID, API_HASH, BOT_TOKEN")

# Initialize client
client = TelegramClient('bot_session', API_ID, API_HASH)


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
    except UsernameOccupiedError:
        return username, False
    except UsernameNotOccupiedError:
        return username, True
    except FloodWaitError as e:
        logger.warning(f"FloodWaitError: waiting {e.seconds} seconds")
        await asyncio.sleep(e.seconds)
        return await check_username(username)
    except Exception as e:
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
        return "No valid usernames found. Please provide 5-32 character usernames."
    
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
    # Skip /start command
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
        await client.start(bot_token=BOT_TOKEN)
        logger.info("Bot started successfully")
        
        me = await client.get_me()
        logger.info(f"Bot username: @{me.username}")
        
        await client.run_until_disconnected()
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
    finally:
        await client.disconnect()


if __name__ == '__main__':
    asyncio.run(main())
