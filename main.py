import os
import asyncio
import discord
from dotenv import load_dotenv
from discord.ext import commands
from datetime import datetime, timezone
from commands import setup_commands
from logic import handle_message, handle_message_edit
from functions import (
    load_monitored_channels,
    save_monitored_channels,
    load_settings,
    save_settings,
    load_webhooks,
    save_webhooks,
    load_tasks,
    save_tasks,
    add_unpin_task,
    add_thread_deletion_task,
    remove_completed_tasks,
    get_due_tasks
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
        self.tasks_file = "tasks.json"
        self.sent_webhook_messages = {}
        self.tasks = {}
        self.load_monitored_channels()
        self.load_settings()
        self.load_webhooks()
        self.load_tasks()

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
            webhooks = {}
        self.webhooks = webhooks
        return self.webhooks

    def save_webhooks(self, webhooks):
        save_webhooks(webhooks, self.webhooks_file)
        self.webhooks = webhooks

    def load_tasks(self):
        self.tasks = load_tasks(self.tasks_file)
        print(f'Loaded Tasks: {self.tasks}')

    def save_tasks(self):
        save_tasks(self.tasks, self.tasks_file)

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        activity = discord.Activity(type=discord.ActivityType.listening, name="to the voices ramble about pins.")

        for guild in self.guilds:
            print(f"Guild Name: {guild.name}, Guild ID: {guild.id}")

# Optional: Leave a specific guild by hardcoding the guild ID
#         
#        guild_id_to_leave = None 
#        guild = self.get_guild(guild_id_to_leave)
#        if guild:
#            await guild.leave()
#            print(f"Left guild: {guild.name} (ID: {guild.id})")
#        else:
#            print(f"Guild with ID {guild_id_to_leave} not found.")

        await self.change_presence(activity=activity)
        await self.reschedule_tasks()  # Run task rescheduling after bot is ready

    async def setup_hook(self):
        await setup_commands(self)
        if guild_id:
            guild = discord.Object(id=guild_id)
            await self.tree.sync(guild=guild)
        else:
            await self.tree.sync()
        self.loop.create_task(self.periodic_task_check())

    async def periodic_task_check(self):
        while True:
            await asyncio.sleep(60)  # Check every minute
            await self.reschedule_tasks()
            self.load_monitored_channels()
            self.load_settings()
            self.load_webhooks()

    async def on_message(self, message):
        await handle_message(self, message)

    async def on_message_edit(self, before, after):
        await handle_message_edit(self, before, after)

    async def execute_unpin_task(self, guild_id, task):
        channel = self.get_channel(task['channel_id'])
        if channel:
            try:
                message = await channel.fetch_message(task['message_id'])
                await message.unpin()
                return True
            except discord.NotFound:
                print(f"Message {task['message_id']} not found in guild {guild_id}, considering it as unpinned.")
                return True
            except discord.Forbidden:
                print(f"No permission to unpin message {task['message_id']} in guild {guild_id}.")
            except Exception as e:
                print(f"Error unpinning message {task['message_id']} in guild {guild_id}: {e}")
        else:
            print(f"Channel {task['channel_id']} not found in guild {guild_id}.")
        
        task['retries'] += 1
        if task['retries'] >= 3: 
            print(f"Task {task} failed after several retries, removing it.")
            return True  
        return False
    
    async def execute_thread_deletion_task(self, guild_id, task):
        channel = self.get_channel(task['channel_id'])
        if channel:
            try:
                thread = await self.fetch_channel(task['thread_id'])
                if isinstance(thread, discord.Thread):
                    await thread.delete()
                    return True
                else:
                    print(f"Channel {task['thread_id']} is not a thread in guild {guild_id}.")
            except discord.NotFound:
                print(f"Thread {task['thread_id']} not found in guild {guild_id}, considering it as deleted.")
                return True
            except discord.Forbidden:
                print(f"No permission to delete thread {task['thread_id']} in guild {guild_id}.")
            except Exception as e:
                print(f"Error deleting thread {task['thread_id']} in guild {guild_id}: {e}")
        else:
            print(f"Channel {task['channel_id']} not found in guild {guild_id}.")
        
        task['retries'] += 1
        if task['retries'] >= 3:
            print(f"Task {task} failed after several retries, removing it.")
            return True  
        return False

    async def reschedule_tasks(self):
        if not self.is_ready():
            print("Bot is not ready yet, delaying task rescheduling")
            return
        
        due_tasks = await get_due_tasks(self.tasks)

        for guild_id, task in due_tasks:
            if task['type'] == 'unpin':
                #print(f"Executing unpin task for guild {guild_id}, message {task['message_id']}")
                success = await self.execute_unpin_task(guild_id, task)
            elif task['type'] == 'thread_deletion':
                #print(f"Executing thread deletion task for guild {guild_id}, thread {task['thread_id']}")
                success = await self.execute_thread_deletion_task(guild_id, task)
            else:
                print(f"Unknown task type: {task['type']}")
                success = False

            if success:
                self.tasks[guild_id] = [t for t in self.tasks[guild_id] if t != task]
                #print(f"Removed completed task for guild {guild_id}")
            else:
                print(f"Task execution failed, will retry if under limit")

        self.save_tasks()

    async def schedule_unpin(self, message, unpin_time):
        await add_unpin_task(self.tasks, message.guild.id, message.channel.id, message.id, unpin_time)
        self.save_tasks()

    async def schedule_thread_deletion(self, message, thread_id, thread_deletion_time):
        await add_thread_deletion_task(self.tasks, message.guild.id, message.channel.id, thread_id, thread_deletion_time)
        self.save_tasks()

    def store_sent_webhook_message(self, original_message_id, webhook_message_id, webhook_url):
        if original_message_id not in self.sent_webhook_messages:
            self.sent_webhook_messages[original_message_id] = []
        self.sent_webhook_messages[original_message_id].append((webhook_message_id, webhook_url))

client = pinBot(command_prefix=None, intents=intents)
client.run(token)