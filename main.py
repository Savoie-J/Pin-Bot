import os
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
        self.monitored_channels = [1278670390230519860, 1278670416541388812, 1278670482044096514, 1278670738437574696]  # List of channel IDs to monitor
        self.max_pins = 10

    async def on_ready(self):
        print(f'Logged in as {self.user}')

    async def on_message(self, message):
        # Check if the message is from FriendlyBot and in one of the monitored channels
        if message.channel.id in self.monitored_channels and message.author.id == 457573832350236672:
            # Check if the message has the embeded button shared by all instance sheets
            if message.components:
                for component in message.components:
                    for button in component.children:
                        if button.label == "Complete the group":
                            # Manage pins: Remove the oldest pin if there are too many
                            pins = await message.channel.pins()
                            if len(pins) >= self.max_pins:
                                await pins[-1].unpin()  # Unpin the oldest message

                            # Pin the new message
                            pinned_message = await message.pin()
                            if pinned_message is None:
                                print("Failed to pin message: returned None")
                            else:
                                print(f"Message pinned: {pinned_message.id}")

                            # Delete the confirmation message of pin sent by discord
                            try:
                                await message.channel.purge(limit=1, check=lambda m: m.author == self.user)
                                print("Deleted bot's confirmation message.")
                            except Exception as e:
                                print(f"Failed to delete bot's message: {e}")

                            # Extract the date from the embed
                            for embed in message.embeds:
                                if embed.description:
                                    start = embed.description.find("`") + 1
                                    end = embed.description.find("`", start)
                                    if start != -1 and end != -1:
                                        date_str = embed.description[start:end]
                                        print(f"Extracted date from embed code block: {date_str}")
                                        date_time = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
                                        date_time = date_time.replace(tzinfo=timezone.utc)
                                        print(f"Extracted datetime: {date_time}")

                                        # Calculate the unpin time
                                        unpin_time = date_time + timedelta(minutes=1)
                                        print(f"Unpin time calculated: {unpin_time}")

                                        # Schedule unpinning
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