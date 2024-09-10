import os
import discord
from dotenv import load_dotenv
from discord.ext import commands
from commands import setup_commands
from functions import load_monitored_channels, save_monitored_channels
from pin_logic import handle_message

load_dotenv()
token = os.getenv("token")

intents = discord.Intents.default()
intents.message_content = True

class pinBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.monitored_channels = {}
        self.max_pins = 50
        self.data_file = "monitored_channels.json"
        self.load_monitored_channels()

    def load_monitored_channels(self):
        self.monitored_channels = load_monitored_channels(self.data_file)

    def save_monitored_channels(self):
        save_monitored_channels(self.monitored_channels, self.data_file)

    async def setup_hook(self):
        await setup_commands(self)
        await self.tree.sync()

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        activity = discord.Activity(type=discord.ActivityType.listening, name="to the voices ramble about pins.")
        await self.change_presence(activity=activity)

    async def on_message(self, message):
        await handle_message(self, message)

client = pinBot(command_prefix="", intents=intents)
client.run(token)