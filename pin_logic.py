import discord
from datetime import datetime, timedelta, timezone
import asyncio

async def handle_message(bot, message):
    if message.guild is None:
        return

    guild_id = message.guild.id

    if guild_id in bot.monitored_channels and message.channel.id in bot.monitored_channels[guild_id] and message.author.id in [457573832350236672, 735842992002433084]:
        print(f"Message from monitored bot detected in channel {message.channel} - {message.channel.id} by bot {message.author} - {message.author.id}.")

        if message.components:
            for component in message.components:
                for button in component.children:
                    if button.label in ["Complete the group", "Complete Team"]:
                        print("Found instance sheet embed button, managing pins...")

                        pins = await message.channel.pins()
                        if len(pins) >= bot.max_pins:
                            await pins[-1].unpin()
                            print("Unpinned the oldest message.")
                        try:
                            print(f"Pinning message: {message.id} in channel: {message.channel} - {message.channel.id}")
                            await message.pin()
                            print(f"Message pinned successfully: {message.id}")
                        except discord.DiscordException as e:
                            print(f"An error occurred while pinning: {e}")

                        try:
                            await message.channel.purge(limit=1, check=lambda m: m.author == bot.user)
                            print("Deleted bot's confirmation message.")
                        except Exception as e:
                            print(f"Failed to delete bot's message: {e}")

                        unpin_time = datetime.now(timezone.utc) + timedelta(hours=1)

                        for embed in message.embeds:
                            if embed.description:
                                if message.author.id == 735842992002433084:  # Elenora bot
                                    gametime_index = embed.description.find("(gametime)")
                                    if gametime_index != -1:
                                        datetime_str = embed.description[:gametime_index].strip().split("\n")[-1].strip()
                                        print(f"Extracted datetime string: {datetime_str}")
                                        try:
                                            date_time = datetime.strptime(datetime_str, "%H:%M %m/%d/%Y")
                                            date_time = date_time.replace(tzinfo=timezone.utc)
                                            print(f"Parsed datetime: {date_time}")
                                            unpin_time = date_time + timedelta(minutes=60)
                                        except ValueError as e:
                                            print(f"Error parsing datetime: {e}. Using default unpin time.")

                                elif message.author.id == 457573832350236672:  # Friendly bot
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

                        await schedule_unpin(message, unpin_time)

async def schedule_unpin(message, unpin_time):
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