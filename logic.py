import re
import discord
import asyncio
import requests
from discord.utils import escape_markdown
from datetime import datetime, timedelta, timezone

async def get_unique_role_mentions(message):
    role_mention_ids = re.findall(r'<@&(\d+)>', message.content)

    ordered_role_mentions = []
    for role_id in role_mention_ids:
        for role in message.role_mentions:
            if str(role.id) == role_id:
                ordered_role_mentions.append(role)
                break
    
    return ordered_role_mentions

async def handle_message(bot, message):
    if message.guild is None:
        return

    guild_id = message.guild.id
    webhooks = bot.load_webhooks()
    settings = bot.settings.get(str(guild_id), {})
    unpin_delay_minutes = settings.get('unpin_time', 60)
    thread_deletion_delay_minutes = settings.get('thread_deletion_time', 60)
    inviteLink = settings.get('invite_link', 'https://discord.com/')

    if (guild_id in bot.monitored_channels and 
    message.channel.id in bot.monitored_channels[guild_id] and 
    message.author.id in [457573832350236672, 735842992002433084, 1284787241943699486, 1286639371038232698]):

        if message.embeds and isinstance(webhooks, dict) and guild_id in webhooks:
            # Capture role mentions from the message and history
            role_mentions = await get_unique_role_mentions(message)

            for webhook_url in webhooks[guild_id]:
                for embed in message.embeds:
                    embed_dict = embed.to_dict()

                    # Construct the message URL and default invite link
                    original_message_url = f"https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}"
                    new_description = f"<a:loading:1286774291689504853> [Join our discord]({inviteLink}) and [come sign up!]({original_message_url})"
                    
                    # Handle role mentions
                    role_mentions_text = ""
                    if role_mentions:
                        role_names = [escape_markdown(role.name) for role in role_mentions]
                        role_mentions_text = ' '.join([f'@{name}' for name in role_names])

                    # Add existing embed description if available
                    existing_description = embed_dict.get('description', '')
                    if existing_description:
                        new_description += f"\n\n{existing_description}"

                    embed_dict['description'] = new_description

                    # Send the webhook with the role mention text outside the embed
                    try:
                        webhook_url_with_wait = webhook_url + "?wait=true"
                        payload = {
                            'content': f"{role_mentions_text}" if role_mentions_text else None,
                            'embeds': [embed_dict]
                        }
                        response = requests.post(webhook_url_with_wait, json=payload)
                        response.raise_for_status()
                        webhook_message_id = response.json()['id']
                        bot.store_sent_webhook_message(message.id, webhook_message_id, webhook_url)
                    except requests.RequestException as e:
                        print(f"Error sending webhook for guild {guild_id} to {webhook_url}: {e}")

        if message.components:
            #print(message)
            for component in message.components:
                for button in component.children:
                    if button.label in ["Complete the group", "Complete group", "Complete Team"]:
                        pins = await message.channel.pins()
                        if len(pins) >= bot.max_pins:
                            await pins[-1].unpin()

                        try:
                            await message.pin()
                        except discord.DiscordException as e:
                            print(f"An error occurred while pinning: {e}")

                        try:
                            await message.channel.purge(limit=1, check=lambda m: m.author == bot.user)
                        except Exception as e:
                            print(f"Failed to delete bot's message: {e}")

                        unpin_time = datetime.now(timezone.utc) + timedelta(minutes=unpin_delay_minutes)
                        thread_deletion_time = datetime.now(timezone.utc) + timedelta(minutes=thread_deletion_delay_minutes)

                        thread_id = None
                        if message.thread:
                            thread_id = message.thread.id

                        for embed in message.embeds:
                            if embed.description:
                                if message.author.id == 735842992002433084:  # Elenora bot
                                    gametime_index = embed.description.find("(gametime)")
                                    if gametime_index != -1:
                                        datetime_str = embed.description[:gametime_index].strip().split("\n")[-1].strip()
                                        try:
                                            date_time = datetime.strptime(datetime_str, "%H:%M %m/%d/%Y")
                                            date_time = date_time.replace(tzinfo=timezone.utc)
                                            unpin_time = date_time + timedelta(minutes=unpin_delay_minutes)
                                            thread_deletion_time = date_time + timedelta(minutes=thread_deletion_delay_minutes)
                                        except ValueError as e:
                                            print(f"Error parsing datetime: {e}. Using default unpin time.")

                                elif message.author.id == 457573832350236672 or 1286639371038232698 or 1284787241943699486:  # Friendly bot or boss bot
                                    start = embed.description.find("`") + 1
                                    end = embed.description.find("`", start)
                                    if start != -1 and end != -1:
                                        date_str = embed.description[start:end]
                                        try:
                                            date_time = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
                                            date_time = date_time.replace(tzinfo=timezone.utc)
                                            unpin_time = date_time + timedelta(minutes=unpin_delay_minutes)
                                            thread_deletion_time = date_time + timedelta(minutes=thread_deletion_delay_minutes)
                                        except ValueError:
                                            print("Date format is incorrect, using default unpin time")

                        asyncio.create_task(schedule_unpin(message, unpin_time))
                        if thread_id:
                            asyncio.create_task(schedule_thread_deletion(message, thread_id, thread_deletion_time))

async def handle_message_edit(bot, before, after):
    # Check if the message belongs to a guild and has embeds
    if after.guild is None or not after.embeds:
        return

    guild_id = after.guild.id
    settings = bot.settings.get(str(guild_id), {})
    inviteLink = settings.get('invite_link', 'https://discord.com/')
    
    # Load the webhooks for the guild
    webhooks = bot.load_webhooks()

    # Check if the message is from a tracked bot and in a monitored channel
    if (guild_id in bot.monitored_channels and 
        after.channel.id in bot.monitored_channels[guild_id] and 
        after.author.id in [457573832350236672, 735842992002433084, 1286639371038232698, 1284787241943699486]):
        
        # If the message was already sent via a webhook, update the existing webhook message
        if after.id in bot.sent_webhook_messages:
            role_mentions = await get_unique_role_mentions(after)

            # Iterate over the saved webhook messages
            for webhook_message_id, webhook_url in bot.sent_webhook_messages[after.id]:
                try:
                    # Fetch the current webhook message details
                    response = requests.get(f"{webhook_url}/messages/{webhook_message_id}")
                    response.raise_for_status()
                    current_webhook_message = response.json()

                    # Get the updated embed from the edited message
                    embed_dict = after.embeds[0].to_dict()

                    # Start constructing the new description
                    new_description = f"<a:loading:1286774291689504853> [Join our discord]({inviteLink}) and [come sign up!]({after.jump_url})"

                    # Add role mentions if any
                    #if role_mentions:
                        #role_names = [escape_markdown(role.name) for role in role_mentions]
                        #role_mentions_text = ' '.join([f'@{name}' for name in role_names])
                        #new_description += f"\n<a:rain:1287411865449922681> {role_mentions_text}"

                    # Append the existing description from the embed if present
                    existing_description = embed_dict.get('description', '')
                    if existing_description:
                        new_description += f"\n\n{existing_description}"

                    # Update the embed's description
                    embed_dict['description'] = new_description

                    # Send a PATCH request to update the webhook message with the new embed
                    response = requests.patch(
                        f"{webhook_url}/messages/{webhook_message_id}",
                        json={'embeds': [embed_dict]}
                    )
                    response.raise_for_status()

                except requests.RequestException as e:
                    print(f"Error updating webhook message for guild {guild_id} at {webhook_url}: {e}")

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
        print(f"Scheduling unpin in {delay} seconds.")
        await asyncio.sleep(delay)
        try:
            await message.unpin()
            print(f"Message unpinned: {message.id}")
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
        print(f"Scheduling thread deletion in {thread_delay} seconds.")
        await asyncio.sleep(thread_delay)
        try:
            guild = message.guild
            thread = discord.utils.get(guild.threads, id=thread_id)
            if thread:
                await thread.delete()
                print(f"Deleted thread: {thread_id}")
            else:
                print(f"Thread {thread_id} not found.")
        except Exception as e:
            print(f"Failed to delete thread: {e}")