import discord
from datetime import datetime, timedelta, timezone
import asyncio

async def handle_message(bot, message):
    if message.guild is None:
        return

    guild_id = message.guild.id

    settings = bot.settings.get(str(guild_id), {})

    unpin_delay_minutes = settings.get('unpin_time', 60)

    thread_deletion_delay_minutes = settings.get('thread_deletion_time', 60)

    if guild_id in bot.monitored_channels and message.channel.id in bot.monitored_channels[guild_id] and message.author.id in [457573832350236672, 735842992002433084]:
        #print(f"Message from monitored bot detected in channel {message.channel} - {message.channel.id} by bot {message.author} - {message.author.id}.")

        if message.components:
            for component in message.components:
                for button in component.children:
                    if button.label in ["Complete the group", "Complete Team"]:
                        #print("Found instance sheet embed button, managing pins...")

                        pins = await message.channel.pins()
                        if len(pins) >= bot.max_pins:
                            await pins[-1].unpin()
                            #print("Unpinned the oldest message.")
                        try:
                            #print(f"Pinning message: {message.id} in channel: {message.channel} - {message.channel.id}")
                            await message.pin()
                            #print(f"Message pinned successfully: {message.id}")
                        except discord.DiscordException as e:
                            print(f"An error occurred while pinning: {e}")

                        try:
                            await message.channel.purge(limit=1, check=lambda m: m.author == bot.user)
                            #print("Deleted bot's confirmation message.")
                        except Exception as e:
                            print(f"Failed to delete bot's message: {e}")

                        unpin_time = datetime.now(timezone.utc) + timedelta(minutes=unpin_delay_minutes)
                        thread_deletion_time = datetime.now(timezone.utc) + timedelta(minutes=thread_deletion_delay_minutes)

                        thread_id = None
                        if message.thread:
                            thread_id = message.thread.id
                            #print(f"Found thread associated with the message: {thread_id}")

                        for embed in message.embeds:
                            if embed.description:
                                if message.author.id == 735842992002433084:  # Elenora bot
                                    gametime_index = embed.description.find("(gametime)")
                                    if gametime_index != -1:
                                        datetime_str = embed.description[:gametime_index].strip().split("\n")[-1].strip()
                                        #print(f"Extracted datetime string: {datetime_str}")
                                        try:
                                            date_time = datetime.strptime(datetime_str, "%H:%M %m/%d/%Y")
                                            date_time = date_time.replace(tzinfo=timezone.utc)
                                            #print(f"Parsed datetime: {date_time}")
                                            unpin_time = date_time + timedelta(minutes=unpin_delay_minutes)
                                            thread_deletion_time = date_time = timedelta(minutes=thread_deletion_delay_minutes)
                                        except ValueError as e:
                                            print(f"Error parsing datetime: {e}. Using default unpin time.")

                                elif message.author.id == 457573832350236672:  # Friendly bot
                                    start = embed.description.find("`") + 1
                                    end = embed.description.find("`", start)
                                    if start != -1 and end != -1:
                                        date_str = embed.description[start:end]
                                        #print(f"Extracted date from embed: {date_str}")
                                        try:
                                            date_time = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
                                            date_time = date_time.replace(tzinfo=timezone.utc)
                                            #print(f"Extracted datetime: {date_time}")
                                            unpin_time = date_time + timedelta(minutes=unpin_delay_minutes)
                                            thread_deletion_time = date_time + timedelta(minutes=thread_deletion_delay_minutes)
                                        except ValueError:
                                            print("Date format is incorrect, using default unpin time")

                        asyncio.create_task(schedule_unpin(message, unpin_time))
                        if thread_id:
                            asyncio.create_task(schedule_thread_deletion(message, thread_id, thread_deletion_time))

async def schedule_unpin(message, unpin_time):
    now = datetime.now(timezone.utc)
    delay = (unpin_time - now).total_seconds()
    
    if delay <= 0:
        print("Unpinning message immediately because the scheduled time is in the past.")
        try:
            await message.unpin()
            #print(f"Message unpinned: {message.id}")
        except Exception as e:
            print(f"Failed to unpin message: {e}")
    else:
        #print(f"Scheduling unpin in {delay} seconds.")
        await asyncio.sleep(delay)
        try:
            await message.unpin()
            #print(f"Message unpinned: {message.id}")
        except Exception as e:
            print(f"Failed to unpin message: {e}")

async def schedule_thread_deletion(message, thread_id, thread_deletion_time):
    now = datetime.now(timezone.utc)
    thread_delay = (thread_deletion_time - now).total_seconds()
    
    if thread_delay <= 0:
        print("Deleting thread immediately because the scheduled time is in the past.")
        try:
            guild = message.guild
            thread = discord.utils.get(guild.threads, id=thread_id)
            if thread:
                await thread.delete()
                #print(f"Deleted thread: {thread_id}")
            else:
                print(f"Thread {thread_id} not found.")
        except Exception as e:
            print(f"Failed to delete thread: {e}")
    else:
        #print(f"Scheduling thread deletion in {thread_delay} seconds.")
        await asyncio.sleep(thread_delay)
        try:
            guild = message.guild
            thread = discord.utils.get(guild.threads, id=thread_id)
            if thread:
                await thread.delete()
                #print(f"Deleted thread: {thread_id}")
            else:
                print(f"Thread {thread_id} not found.")
        except Exception as e:
            print(f"Failed to delete thread: {e}")