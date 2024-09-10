import os
import json
import discord
import asyncio
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

load_dotenv()
token = os.getenv("token")

intents = discord.Intents.default()
intents.message_content = True

class pinBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.monitored_channels = {}
        self.max_pins = 10
        self.tree = discord.app_commands.CommandTree(self)
        self.data_file = "monitored_channels.json"
        self.load_monitored_channels()

    def load_monitored_channels(self):
        try:
            with open(self.data_file, 'r') as f:
                self.monitored_channels = json.load(f)
                # Convert keys and values to integers if they are loaded as strings
                self.monitored_channels = {
                    int(guild_id): [int(channel_id) for channel_id in channels]
                    for guild_id, channels in self.monitored_channels.items()
                }
                print("Loaded monitored channels from file:", self.monitored_channels)
        except FileNotFoundError:
            print("No saved monitored channels file found, starting fresh.")
            self.monitored_channels = {}
        except json.JSONDecodeError:
            print("Error decoding JSON from the file, starting fresh.")
            self.monitored_channels = {}

    def save_monitored_channels(self):
        try:
            with open(self.data_file, 'w') as f:
                # Make sure to store as integers
                json.dump(
                    {str(k): [str(ch) for ch in v] for k, v in self.monitored_channels.items()},
                    f, indent=4
                )
                print("Saved monitored channels to file:", self.monitored_channels)
        except Exception as e:
            print(f"Failed to save monitored channels: {e}")


    async def setup_commands(self):
        @self.tree.command(name="addchannel", description="Add a channel to the monitored list")
        @discord.app_commands.describe(channel="The channel to add")
        async def add_channel(interaction: discord.Interaction, channel: discord.TextChannel):
            guild_id = interaction.guild.id
            if guild_id not in self.monitored_channels:
                self.monitored_channels[guild_id] = []

            if channel.id not in self.monitored_channels[guild_id]:
                print(f"Adding channel {channel.id} to monitored list.")
                self.monitored_channels[guild_id].append(channel.id)
                self.save_monitored_channels()  # Save the updated list
                await interaction.response.send_message(f"Channel <#{channel.id}> added to the monitored list.", ephemeral=True)
            else:
                await interaction.response.send_message("Channel is already monitored.", ephemeral=True)

        @self.tree.command(name="removechannel", description="Remove a channel from the monitored list")
        @discord.app_commands.describe(channel="The channel to remove")
        async def remove_channel(interaction: discord.Interaction, channel: discord.TextChannel):
            guild_id = interaction.guild.id
            if guild_id in self.monitored_channels and channel.id in self.monitored_channels[guild_id]:
                self.monitored_channels[guild_id].remove(channel.id)
                self.save_monitored_channels()  # Save the updated list
                await interaction.response.send_message(f"Channel <#{channel.id}> removed from the monitored list.", ephemeral=True)
            else:
                await interaction.response.send_message("Channel is not monitored.", ephemeral=True)

        @self.tree.command(name="listchannels", description="List all monitored channels")
        async def list_channels(interaction: discord.Interaction):
            guild_id = interaction.guild.id
            print(f"Fetching monitored channels for guild ID: {guild_id}")
            if guild_id in self.monitored_channels:
                print(f"Monitored channels found for guild ID {guild_id}: {self.monitored_channels[guild_id]}")
                channel_mentions = [f"<#{channel_id}>" for channel_id in self.monitored_channels[guild_id]]
                channels_list = ", ".join(channel_mentions) if channel_mentions else "No channels are currently monitored."
            else:
                channels_list = "No channels are currently monitored."
            print(f"Monitored Channels: {channels_list}")
            await interaction.response.send_message(f"Monitored Channels: {channels_list}", ephemeral=True)

    async def sync_commands(self):
        try:
            await self.tree.sync()  # Global sync
            print(f"Successfully synced {len(self.tree.get_commands())} command(s).")
        except Exception as e:
            print(f"Failed to sync commands: {e}")

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        await self.setup_commands()
        await self.sync_commands()

        activity = discord.Activity(type=discord.ActivityType.listening, name="to the voices ramble about pins.")
        await self.change_presence(activity=activity)

    async def on_message(self, message):
        if message.guild is None:
            return

        guild_id = message.guild.id
        
        # Check if the channel is in the monitored list for the specific guild
        if guild_id in self.monitored_channels and message.channel.id in self.monitored_channels[guild_id] and message.author.id == 457573832350236672:
            print(f"Message from monitored bot detected in channel {message.channel} - {message.channel.id}.")
            if message.components:
                for component in message.components:
                    for button in component.children:
                        if button.label == "Complete the group":
                            print("Found 'Complete the group' button, managing pins...")
                            pins = await message.channel.pins()
                            if len(pins) >= self.max_pins:
                                await pins[-1].unpin()
                                print("Unpinned the oldest message.")
                            try:
                                # Log additional details about the message, channel, and bot
                                print(f"Pinning message: {message.id} in channel: {message.channel} - {message.channel.id}")
                                #print(f"Bot: {self.user.id}")

                                await message.pin()
                                print(f"Message pinned successfully: {message.id}")
                            except discord.DiscordException as e:
                                print(f"An error occurred while pinning: {e}")

                            try:
                                await message.channel.purge(limit=1, check=lambda m: m.author == self.user)
                                print("Deleted bot's confirmation message.")
                            except Exception as e:
                                print(f"Failed to delete bot's message: {e}")

                            # Default unpin time to 1 hour from now
                            unpin_time = datetime.now(timezone.utc) + timedelta(hours=1)
                            
                            for embed in message.embeds:
                                if embed.description:
                                    start = embed.description.find("`") + 1
                                    end = embed.description.find("`", start)
                                    if start != -1 and end != -1:
                                        date_str = embed.description[start:end]
                                        print(f"Extracted date from embed: {date_str}")
                                        try:
                                            date_time = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
                                            date_time = date_time.replace(tzinfo=timezone.utc)
                                            print(f"Extracted datetime: {date_time}")
                                            unpin_time = date_time + timedelta(minutes=60)
                                        except ValueError:
                                            print("Date format is incorrect, using default unpin time")
                                    else:
                                        print("Date not found in embed description, using default unpin time")
                            
                            print(f"Unpin time calculated: {unpin_time}")
                            await self.schedule_unpin(message, unpin_time)

    async def schedule_unpin(self, message, unpin_time):
        now = datetime.now(timezone.utc)
        delay = (unpin_time - now).total_seconds()
        if delay > 0:
            print(f"Scheduling unpin in {delay} seconds.")
            await asyncio.sleep(delay)
            try:
                await message.unpin()
                print(f"Message unpinned: {message.id}")
            except Exception as e:
                print(f"Failed to unpin message: {e}")

client = pinBot(intents=intents)
client.run(token)