import asyncio
import base64
from collections import deque

from aiohttp import ClientSession
from starlette.applications import Starlette
from starlette.config import Config
from starlette.routing import WebSocketRoute
from starlette.websockets import WebSocket

config = Config(".env")

BOT_TOKEN = config("BOT_TOKEN")
CHANNEL_ID = config("CHANNEL_ID")

AUDIO_BUFFER = deque()


async def send_discord_message(message: str) -> str:
    async with ClientSession() as session:
        async with session.post(
            f"https://discord.com/api/channels/{CHANNEL_ID}/messages",
            json={"content": message},
            headers={
                "Authorization": f"Bot {BOT_TOKEN}",
                # dummy values
                "User-Agent": "ProxyBot (http://some.url, v0.1)",
            },
        ) as response:
            return await response.text()


async def phone_connect(websocket: WebSocket) -> None:
    await websocket.accept()
    await send_discord_message(
        "A call has come in, use `$connect` to connect them to the voice channel!"  # noqa: E501
    )

    try:
        while True:
            payload: dict = await websocket.receive_json()

            if payload.get("event") == "media":
                # audio/x-mulaw with a sample rate of 8000 and base64 encoded
                # Per https://www.twilio.com/docs/voice/twiml/stream#message-media-to-twilio  # noqa: E501
                snippet = payload["media"]["payload"]
                AUDIO_BUFFER.append(base64.b64decode(snippet))

                # Echo back the packet we just received, resulting in the
                # caller talking to themselves.
                await websocket.send_json(
                    {
                        "event": "media",
                        "streamSid": payload.get("streamSid"),
                        "media": {
                            "payload": snippet,
                        },
                    }
                )
    finally:
        # FIXME: don't think this is the right way to handle this.
        await websocket.close()


async def discord_connect(websocket: WebSocket) -> None:
    await websocket.accept()

    # Clear out any unconsumed packets from the buffer so that
    # Discord gets the earliest audio AFTER connection.
    AUDIO_BUFFER.clear()

    while True:
        try:
            chunk = AUDIO_BUFFER.popleft()
            await websocket.send_bytes(chunk)
        except IndexError:
            # Unblock the event loop.
            await asyncio.sleep(0)


routes = [
    WebSocketRoute("/phone", phone_connect),
    WebSocketRoute("/discord", discord_connect),
]
app = Starlette(debug=True, routes=routes)
