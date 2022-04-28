import subprocess
import wave

import discord
import websockets
from starlette.config import Config

config = Config(".env")

BOT_TOKEN = config("BOT_TOKEN")
VOICE_CHANNEL_ID = config("VOICE_CHANNEL_ID")
PROXY_SERVER_URL = config(
    "PROXY_SERVER_URL",
    default="ws://127.0.0.1:8000/discord",
)


class ProxyClient(discord.Client):
    async def connect_to_voice_channel(self):
        voice_channel: discord.VoiceChannel = await self.fetch_channel(VOICE_CHANNEL_ID)
        voice_client: discord.VoiceClient = await voice_channel.connect()

        # Okay, don't ask me how this works but we're basically constructing
        # a pipe from the phone call to ffmpeg to Discord. The first step to
        # doing this is to pass subprocess.PIPE in as the source.
        audio_pipe = discord.FFmpegOpusAudio(subprocess.PIPE, pipe=True)

        with wave.open(audio_pipe._process.stdin, "wb") as f:
            # Send wav headers to ffmpeg.
            f.setnchannels(1)
            f.setsampwidth(1)
            f.setframerate(8000)
            f.setnframes(14400000)  # 30 minute time limit :(

            # For some reason, this works. ffmpeg will convert the audio
            # snippets as they come in and emit silence otherwise.
            voice_client.play(audio_pipe)

            async with websockets.connect(PROXY_SERVER_URL) as ws:
                while True:
                    snippet = await ws.recv()

                    # We can't use .writeframes() here as an Illegal seek
                    # to rewrite the header will happen.
                    f.writeframesraw(snippet)

    async def on_ready(self):
        print(f"Logged in as {self.user}")

    async def on_message(self, message):
        if message.author == client.user:
            return

        if message.content.startswith("$connect"):
            await self.connect_to_voice_channel()


if __name__ == "__main__":
    client = ProxyClient()
    client.run(BOT_TOKEN)
