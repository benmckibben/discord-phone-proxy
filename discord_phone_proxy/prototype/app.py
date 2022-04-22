import base64
import wave

from aiohttp import ClientSession
from starlette.applications import Starlette
from starlette.config import Config
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.routing import Route, WebSocketRoute
from starlette.websockets import WebSocket


config = Config(".env")

BOT_TOKEN = config("BOT_TOKEN")
CHANNEL_ID = config("CHANNEL_ID")


async def send_discord_message(message: str):
    async with ClientSession() as session:
        async with session.post(
            f"https://discord.com/api/channels/{CHANNEL_ID}/messages",
            json={"content": f"```json\n{message}\n```"},
            headers={
                "Authorization": f"Bot {BOT_TOKEN}",
                "User-Agent": "ProxyBot (http://some.url, v0.1)",
            }
        ) as response:
            return await response.text()


def index(request: Request) -> PlainTextResponse:
    return PlainTextResponse("Hiya")

async def echo(websocket: WebSocket) -> None:
    await websocket.accept()
    await send_discord_message("A new call has been accepted!")
    try:
        with wave.open("call.wav", "wb") as f:
            f.setnchannels(1)
            f.setsampwidth(1)
            f.setframerate(8000)

            while True:
                payload: dict = await websocket.receive_json()
                
                if payload.get("event") == "media":
                    snippet = payload["media"]["payload"]
                    f.writeframes(base64.b64decode(snippet))
                    await websocket.send_json({
                        "event": "media",
                        "streamSid": payload.get("streamSid"),
                        "media": {
                            # audio/x-mulaw with a sample rate of 8000 and base64 encoded
                            # Per https://www.twilio.com/docs/voice/twiml/stream#message-media-to-twilio
                            "payload": snippet,
                        }
                    })
    finally:
        await websocket.close()


routes = [
    Route("/", index),
    WebSocketRoute("/echo", echo),
]
app = Starlette(debug=True, routes=routes)
