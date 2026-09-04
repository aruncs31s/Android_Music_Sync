"""
Telegram Deezload Bot Integration Module.

Automates sending Spotify links to Telegram music download bots (such as @deezload / @DeezloadBot)
using Telethon or Pyrogram, and saving received audio files into songs/download/.
"""
import os
import sys
import asyncio
from typing import Optional

DEFAULT_BOT = "@deezloadbot"

def is_telegram_client_available() -> bool:
    """Check if Telethon library is installed."""
    try:
        import telethon
        return True
    except ImportError:
        return False

async def _download_from_telegram_bot_async(
    spotify_url: str,
    output_dir: str = "songs/download",
    api_id: Optional[int] = None,
    api_hash: Optional[str] = None,
    bot_username: str = DEFAULT_BOT,
    session_name: str = "deezload_session"
) -> Optional[str]:
    """
    Async implementation using Telethon client to send link to Telegram Deezload bot and download audio.
    """
    if not is_telegram_client_available():
        print("Telethon library is not installed. Install with: pip install telethon", file=sys.stderr)
        return None

    from telethon import TelegramClient, events

    env_api_id = os.getenv("TELEGRAM_API_ID")
    env_api_hash = os.getenv("TELEGRAM_API_HASH")

    final_api_id = api_id or (int(env_api_id) if env_api_id else None)
    final_api_hash = api_hash or env_api_hash

    if not final_api_id or not final_api_hash:
        print("Missing TELEGRAM_API_ID or TELEGRAM_API_HASH environment variables.", file=sys.stderr)
        return None

    os.makedirs(output_dir, exist_ok=True)
    client = TelegramClient(session_name, final_api_id, final_api_hash)
    downloaded_path = None

    await client.start()

    print(f"Connected to Telegram. Sending link to {bot_username}...", file=sys.stderr)

    # Event handler waiting for audio document response from deezload bot
    event_future = asyncio.get_event_loop().create_future()

    @client.on(events.NewMessage(chats=bot_username))
    def handle_bot_reply(event):
        if event.message.media and (event.message.audio or event.message.document):
            if not event_future.done():
                event_future.set_result(event.message)

    # Send Spotify link to bot
    await client.send_message(bot_username, spotify_url)

    try:
        # Wait up to 60 seconds for bot reply
        reply_message = await asyncio.wait_for(event_future, timeout=60.0)
        print("Received audio file from Deezload bot. Downloading to songs/download/...", file=sys.stderr)

        # Download media file into output_dir
        downloaded_path = await reply_message.download_media(file=output_dir)
        print(f"Deezload download complete: {downloaded_path}", file=sys.stderr)
    except asyncio.TimeoutError:
        print(f"Timeout waiting for reply from {bot_username}.", file=sys.stderr)
    finally:
        await client.disconnect()

    return downloaded_path

def download_via_deezload(
    spotify_url: str,
    output_dir: str = "songs/download",
    bot_username: str = DEFAULT_BOT
) -> Optional[str]:
    """
    Synchronous wrapper to download Spotify link via Telegram Deezload bot.
    """
    try:
        return asyncio.run(_download_from_telegram_bot_async(spotify_url, output_dir=output_dir, bot_username=bot_username))
    except Exception as e:
        print(f"Error in Deezload Telegram download: {e}", file=sys.stderr)
        return None
