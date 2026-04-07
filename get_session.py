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
