import asyncio
import base64
import io
from subprocess import call
import threading
import wave
from collections import deque

from aiohttp import ClientSession
from starlette.applications import Starlette
from starlette.config import Config
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.routing import Route, WebSocketRoute
from starlette.websockets import WebSocket

from discord_phone_proxy.prototype.bot import MyClient


config = Config(".env")

BOT_TOKEN = config("BOT_TOKEN")
CHANNEL_ID = config("CHANNEL_ID")

call_bytes_buffer = deque()


async def send_discord_message(message: str):
    async with ClientSession() as session:
        async with session.post(
            f"https://discord.com/api/channels/{CHANNEL_ID}/messages",
            json={"content": f"```json\n{message}\n```"},
            headers={
                "Authorization": f"Bot {BOT_TOKEN}",
                "User-Agent": "ProxyBot (http://some.url, v0.1)",
            },
        ) as response:
            return await response.text()


def index(request: Request) -> PlainTextResponse:
    return PlainTextResponse("Hiya")


async def echo(websocket: WebSocket) -> None:
    await websocket.accept()
    await send_discord_message("A new call has been accepted!")

    try:
        while True:
            payload: dict = await websocket.receive_json()

            if payload.get("event") == "media":
                # audio/x-mulaw with a sample rate of 8000 and base64 encoded
                # Per https://www.twilio.com/docs/voice/twiml/stream#message-media-to-twilio
                snippet = payload["media"]["payload"]
                call_bytes_buffer.append(base64.b64decode(snippet))
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
        await websocket.close()


async def discord_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()

    # Send wav headers.
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(1)
        f.setframerate(8000)

    wav_buffer.seek(0)
    # await websocket.send_bytes(wav_buffer.read())

    call_bytes_buffer.clear()

    while True:
        try:
            chunk = call_bytes_buffer.popleft()
            # print("Sending from buffer!")
            await websocket.send_bytes(chunk)
        except IndexError:
            # print("Nothing in the buffer :(")
            await asyncio.sleep(0.02)


routes = [
    Route("/", index),
    WebSocketRoute("/echo", echo),
    WebSocketRoute("/discord", discord_endpoint),
]
app = Starlette(debug=True, routes=routes)
