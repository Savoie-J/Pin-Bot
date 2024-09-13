import os
import discord
from dotenv import load_dotenv
from discord.ext import commands
from commands import setup_commands
from functions import load_monitored_channels, save_monitored_channels, load_settings, save_settings
from logic import handle_message

load_dotenv()
token = os.getenv("token")
guild_id = None #for syncing to a specific guild during testing

intents = discord.Intents.default()
intents.message_content = True

class pinBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_pins = 50
        self.monitored_channels = {}
        self.settings = {}
        self.data_file = "monitored_channels.json"
        self.settings_file = "settings.json"
        self.load_monitored_channels()
        self.load_settings()

    def load_monitored_channels(self):
        self.monitored_channels = load_monitored_channels(self.data_file)

    def save_monitored_channels(self):
        save_monitored_channels(self.monitored_channels, self.data_file)

    def load_settings(self):
        self.settings = load_settings(self.settings_file) 

    def save_settings(self):
        save_settings(self.settings, self.settings_file)

    async def setup_hook(self):
        await setup_commands(self)
        # Sync commands only to the specified guild
        if guild_id:
            guild = discord.Object(id=guild_id)
            await self.tree.sync(guild=guild)
            #print(f"Commands synced to guild: {guild_id}")
        else:
            await self.tree.sync()
            #print("Commands synced globally.")

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        activity = discord.Activity(type=discord.ActivityType.listening, name="to the voices ramble about pins.")
        await self.change_presence(activity=activity)

    async def on_message(self, message):
        await handle_message(self, message)

client = pinBot(command_prefix=None, intents=intents)
client.run(token)