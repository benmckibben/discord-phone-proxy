from asyncio import sleep

import discord
from starlette.config import Config

config = Config(".env")

BOT_TOKEN = config("BOT_TOKEN")
VC_ID = config("VC_ID")


class MyClient(discord.Client):
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

            while True:
                await sleep(1)
                await message.channel.send("Still connected")


if __name__ == "__main__":
    client = MyClient()
    client.run(BOT_TOKEN)
