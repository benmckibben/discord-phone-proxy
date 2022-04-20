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
            json={"content": message},
            headers={
                "Authorization": f"Bot {BOT_TOKEN}",
                "User-Agent": "ProxyBot (http://some.url, v0.1)",
            }
        ) as response:
            print(response.status)
            return await response.text()


def index(request: Request) -> PlainTextResponse:
    return PlainTextResponse("Hiya")

async def echo(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            payload: dict = await websocket.receive_json()
            result = await send_discord_message(payload.get("message"))
            await websocket.send_json({"success": True, "response": result})
    except Exception:
        await websocket.send_json({"success": False})
        await websocket.close()
        raise


routes = [
    Route("/", index),
    WebSocketRoute("/echo", echo),
]
app = Starlette(debug=True, routes=routes)
