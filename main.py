import os
import discord
from dotenv import load_dotenv
from discord.ext import commands
from commands import setup_commands
from logic import handle_message, handle_message_edit  # Import the function from logic
from functions import (
    load_monitored_channels,
    save_monitored_channels,
    load_settings,
    save_settings,
    load_webhooks,
    save_webhooks
)

load_dotenv()
token = os.getenv("token")
guild_id = None  # For syncing to a specific guild during testing

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

class pinBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_pins = 50
        self.monitored_channels = {}
        self.settings = {}
        self.webhooks = {} 
        self.data_file = "monitored_channels.json"
        self.settings_file = "settings.json"
        self.webhooks_file = "webhooks.json"
        self.sent_webhook_messages = {}
        self.load_monitored_channels()
        self.load_settings()
        self.load_webhooks()

    def load_monitored_channels(self):
        self.monitored_channels = load_monitored_channels(self.data_file)

    def save_monitored_channels(self):
        save_monitored_channels(self.monitored_channels, self.data_file)

    def load_settings(self):
        self.settings = load_settings(self.settings_file)

    def save_settings(self):
        save_settings(self.settings, self.settings_file)

    def load_webhooks(self):
        webhooks = load_webhooks(self.webhooks_file)
        if not isinstance(webhooks, dict):
            print(f"Webhooks is not a dictionary, initializing empty dict")
            webhooks = {}
        self.webhooks = webhooks
        return self.webhooks

    def save_webhooks(self, webhooks):
        save_webhooks(webhooks, self.webhooks_file)
        self.webhooks = webhooks

    async def setup_hook(self):
        await setup_commands(self)
        # Sync commands only to the specified guild
        if guild_id:
            guild = discord.Object(id=guild_id)
            await self.tree.sync(guild=guild)
        else:
            await self.tree.sync()

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        activity = discord.Activity(type=discord.ActivityType.listening, name="to the voices ramble about pins.")
        await self.change_presence(activity=activity)

    async def on_message(self, message):
        await handle_message(self, message)

    async def on_message_edit(self, before, after):
        await handle_message_edit(self, before, after)

    def store_sent_webhook_message(self, original_message_id, webhook_message_id, webhook_url):
        if original_message_id not in self.sent_webhook_messages:
            self.sent_webhook_messages[original_message_id] = []
        self.sent_webhook_messages[original_message_id].append((webhook_message_id, webhook_url))

client = pinBot(command_prefix=None, intents=intents)
client.run(token)