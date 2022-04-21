from asyncio import sleep, gather
from time import perf_counter

import discord
from starlette.config import Config

config = Config(".env")

BOT_TOKEN = config("BOT_TOKEN")
VC_ID = config("VC_ID")


class MyClient(discord.Client):
    async def output_audio_loop(self, channel):
        FRAME_LENGTH = 20
        DELAY = FRAME_LENGTH / 1000.0

        while True:
            i = 0
            self.no_audio = discord.FFmpegOpusAudio("no.wav")
            
            start = perf_counter()
            loops = 0

            while True:
                loops += 1
                chunk =  self.no_audio.read()
                if not chunk:
                    break

                self.voice_client.send_audio_packet(chunk, encode=False)

                next_time = start + DELAY * loops
                delay = max(0, DELAY + (next_time - perf_counter()))
                await sleep(delay)

    
            await channel.send("Just finished playing audio")
            await sleep(3)

    async def still_connected_loop(self, channel):
        while True:
            await channel.send("Still connected")
            await sleep(1)

    async def on_ready(self):
        print('We have logged in as {0.user}'.format(client))

    async def on_message(self, message):
        if message.author == client.user:
            return

        if message.content.startswith('$hello'):
            await message.channel.send('Hello!')

        if message.content.startswith("$play"):
            source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio("no.wav"))
            self.voice_client.play(source, after=lambda e: print(f"Player error: {e}") if e else None)
            await message.channel.send("Playing")

        if message.content.startswith("$connect"):
            self.vc: discord.VoiceChannel = await self.fetch_channel(VC_ID)
            self.voice_client: discord.VoiceClient = await self.vc.connect()

            await gather(self.output_audio_loop(message.channel), self.still_connected_loop(message.channel))


if __name__ == "__main__":
    client = MyClient()
    client.run(BOT_TOKEN)
