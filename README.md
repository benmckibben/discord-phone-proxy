# discord-phone-proxy
System using [Starlette](https://www.starlette.io/) and [discord.py](https://discordpy.readthedocs.io/en/stable/) to proxy [Twilio](https://www.twilio.com/) phone calls into [Discord](https://discord.com/) voice channels.

## Proof-of-concept / incompleteness disclaimer
This project is unfinished, and will remain so indefinitely as my goal was to see how far I could push linking phone calls and Discord voice channels. As such, a full-featured proxy is absent from this repo, and I only claim the following functionality:

*This system allows a user to call a Twilio phone number and have their voice (low quality and very distorted) transmitted to a Discord voice channel.*

This system currently is NOT:
* Production-ready. At all.
* Able to relay the output of the Discord voice channel back to the phone call. As far as I can tell, discord.py and Discord don't supply APIs for receiving voice data from a voice channel connection.
* Able to support multiple users / channels, mainly due to the shared buffer mechanism in the Starlette app.
* Efficient. There is noticeable delay between speaking into the phone and hearing that audio in the call.

That said, I had fun with this experiment. :)

## Running the system
Due to the more experimental nature of this project, I won't go into too much detail on setup instructions as I would with a completed project. Feel free to raise issues with questions.

Before starting, be aware that this system requires a Discord bot account and a Twilio phone number; the former is free, but the latter costs money.

1. Use [Poetry](https://python-poetry.org/) to install dependencies.
1. Set the following environment variables or specify them in a `.env` file:
    * `BOT_TOKEN`: your Discord bot token
    * `VOICE_CHANNEL_ID`: Discord ID of the voice channel to transmit to
    * `TEXT_CHANNEL_ID`: Discord ID of the text channel for call connection notifications
    * `PROXY_SERVER_URL` (optional): URL of the websocket endpoint exposed by the Starlette app that the discord.py bot will connect to.
1. Spin up the Starlette app with `poetry run uvicorn --reload discord_phone_proxy.prototype.app:app` and expose it to the internet (Twilio opens the websockets). I use [ngrok](https://ngrok.com/) from my local machine, but you can just as easily use an EC2 instance or something.
1. In a separate terminal (or host if you really want to), spin up the Discord.py bot with `poetry run python -m discord_phone_proxy.prototype.bot`. You do NOT need to expose this component to the internet.
1. Configure a Twilio phone number to execute `twiml.xml` (replacing the hostname with the hostname of the Starlette app) on an incoming call. Reference Twilio's docs to learn how to accomplish this.

## Usage
Once the system is up and running, you should be able to do the following:

1. Make a phone call to your Twilio number. `TEXT_CHANNEL_ID` should get a message that a call has come in.
1. Speak into the phone. You should hear your own voice echoed back to you, proving that we're successfully interacting with a bidirectional Twilio call.
1. Send `$connect` to a text channel. The bot should move into `VOICE_CHANNEL_ID`.
1. Turn down your volume, and join `VOICE_CHANNEL_ID`. You should be able to hear a very loud and distorted version of what you're saying over the phone.
1. Hang up the phone. The noise should stop.

## Contributing
If you want to help with any of the missing pieces of this project, feel free to submit pull requests! I'm not too concerned about providing guidelines given how early-stage this project is, but black, isort, and flake8 are available as dev dependencies.