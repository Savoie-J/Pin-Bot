import os
import discord
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("token")

intents = discord.Intents.default()
intents.message_content = True

class pinBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.monitored_channels = [1278670390230519860, 1278670416541388812, 1278670482044096514, 1278670738437574696]
        self.max_pins = 10

    async def on_ready(self):
        print(f'Logged in as {self.user}')

    async def on_message(self, message):
        if message.channel.id in self.monitored_channels and message.author.id == 457573832350236672:
            if message.components:
                for component in message.components:
                    for button in component.children:
                        if button.label == "Complete the group":
                            pins = await message.channel.pins()
                            if len(pins) >= self.max_pins:
                                await pins[-1].unpin() 

                            await message.pin()

                            try:
                                await message.channel.purge(limit=1, check=lambda m: m.author == self.user)
                            except Exception as e:
                                print(f"Failed to delete bot's message: {e}")

client = pinBot(intents=intents)
client.run(token)