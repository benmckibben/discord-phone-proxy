import subprocess
import wave
from contextlib import AsyncExitStack
from asyncio import sleep, gather
from time import perf_counter

import discord
import websockets
from starlette.config import Config

config = Config(".env")

BOT_TOKEN = config("BOT_TOKEN")
VC_ID = config("VC_ID")


class MyClient(discord.Client):
    async def connect_to_vc(self):
        self.vc: discord.VoiceChannel = await self.fetch_channel(VC_ID)
        self.voice_client: discord.VoiceClient = await self.vc.connect()

        async with AsyncExitStack() as stack:
            self.call_ws = await stack.enter_async_context(
                websockets.connect("ws://127.0.0.1:8000/discord")
            )
            self.call_ws_closer = stack.pop_all().aclose

    async def receive_wav_file(self):
        with wave.open("call2.wav", "wb") as f:
            f.setnchannels(1)
            f.setsampwidth(1)
            f.setframerate(8000)
            while True:
                snippet = await self.call_ws.recv()
                f.writeframes(snippet)

    async def output_audio_loop(self):
        FRAME_LENGTH = 20
        DELAY = FRAME_LENGTH / 1000.0

        no_audio = discord.FFmpegOpusAudio(subprocess.PIPE, pipe=True)

        with wave.open(no_audio._process.stdin, "wb") as f:
            f.setnchannels(1)
            f.setsampwidth(1)
            f.setframerate(8000)
            f.setnframes(1000000)

            self.voice_client.play(
                no_audio, after=lambda e: print(f"Player error: {e}") if e else None
            )
            while True:
                snippet = await self.call_ws.recv()
                f.writeframesraw(snippet)

    async def still_connected_loop(self, channel):
        while True:
            await channel.send("Still connected")
            await sleep(1)

    async def on_ready(self):
        print(f"We have logged in as {self.user}")

    async def on_message(self, message):
        if message.author == client.user:
            return

        if message.content.startswith("$hello"):
            await message.channel.send("Hello!")

        if message.content.startswith("$play"):
            source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio("no.wav"))
            self.voice_client.play(
                source, after=lambda e: print(f"Player error: {e}") if e else None
            )
            await message.channel.send("Playing")

        if message.content.startswith("$connect"):
            await self.connect_to_vc()
            await self.output_audio_loop()


if __name__ == "__main__":
    client = MyClient()
    client.run(BOT_TOKEN)
