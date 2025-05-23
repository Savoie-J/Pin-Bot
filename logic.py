import re
import discord
import asyncio
import requests
from discord.utils import escape_markdown
from datetime import datetime, timedelta, timezone

async def handle_message(bot, message):
    if message.guild is None:
        return

    guild_id = message.guild.id
    webhooks = bot.webhooks
    settings = bot.settings.get(str(guild_id), {})
    unpin_delay_minutes = settings.get('unpin_time', 60)
    thread_deletion_delay_minutes = settings.get('thread_deletion_time', 60)
    inviteLink = settings.get('invite_link', 'https://discord.com/')
    force_thread_creation = settings.get('force_thread_creation', False)

    if (guild_id in bot.monitored_channels and 
    message.channel.id in bot.monitored_channels[guild_id] and 
    message.author.id in [457573832350236672, 735842992002433084, 1284787241943699486, 1286639371038232698]):

        if message.embeds and isinstance(webhooks, dict) and guild_id in webhooks:
            # Capture role mentions from the message and history
            role_mentions = await get_unique_role_mentions(message)

            if guild_id in bot.sent_webhook_messages and message.id in bot.sent_webhook_messages[guild_id]:
                print(f"Skipping duplicate webhook for message {message.id}")
            else:
                bot.sent_webhook_messages.setdefault(guild_id, set()).add(message.id)  # Mark message as sent
                for webhook_url in webhooks[guild_id]:
                    if not message.embeds:
                        continue  # Skip if no embeds are found

                    embed = message.embeds[0]  # Send only the first embed to avoid duplicates
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
                        
                        # Store the webhook message
                        bot.store_sent_webhook_message(message.id, webhook_message_id, webhook_url)
                        
                       # Extract the webhook ID from the URL
                        webhook_url_pattern = r"https://discord.com/api/webhooks/(?P<id>\d+)/(?P<token>[\w-]+)"
                        match = re.match(webhook_url_pattern, webhook_url)
                        if match:
                            webhook_id = match.group('id')
                            # Fetch the webhook to get its channel ID
                            webhook = await bot.fetch_webhook(webhook_id)
                            webhook_channel_id = webhook.channel_id

                            # Fetch the channel where the webhook was sent
                            webhook_channel = bot.get_channel(webhook_channel_id)
                            if webhook_channel and isinstance(webhook_channel, discord.TextChannel):
                                try:
                                    # Fetch the webhook message using its ID
                                    webhook_message = await webhook_channel.fetch_message(webhook_message_id)

                                    # Check if the channel is an announcement (news) channel and publish the message
                                    if webhook_channel.is_news():
                                        await webhook_message.publish()
                                        #print(f"Published message {webhook_message_id} in channel {webhook_channel.id}.")
                                except discord.Forbidden:
                                    print(f"Failed to publish the message in channel {webhook_channel.id}. The bot may lack the required permissions.")
                                except discord.HTTPException as e:
                                    print(f"An error occurred while attempting to publish the message: {e}")
                                except discord.NotFound:
                                    print(f"Webhook message {webhook_message_id} not found in channel {webhook_channel.id}.")
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

                                            if not thread_id and force_thread_creation:
                                                thread_name = f"{date_time.strftime('%H:%M - %m/%d')}"
                                                thread = await message.create_thread(name=thread_name)
                                                thread_id = thread.id

                                                if message.role_mentions:
                                                    ping_message = await thread.send(message.role_mentions[0].mention)
                                                    await ping_message.delete()
                                            
                                            elif thread_id:
                                                thread = message.channel.get_thread(thread_id)
                                                new_name = f"{date_time.strftime('%H:%M - %m/%d - ')} {thread.name}"
                                                await thread.edit(name=new_name)

                                        except ValueError as e:
                                            print(f"Error parsing datetime: {e}. Using default unpin time.")

                                elif message.author.id in [457573832350236672, 1286639371038232698, 1284787241943699486]: # Friendly bot or boss bot
                                    start = embed.description.find("`") + 1
                                    end = embed.description.find("`", start)
                                    if start != -1 and end != -1:
                                        date_str = embed.description[start:end]
                                        try:
                                            date_time = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
                                            date_time = date_time.replace(tzinfo=timezone.utc)
                                            unpin_time = date_time + timedelta(minutes=unpin_delay_minutes)
                                            thread_deletion_time = date_time + timedelta(minutes=thread_deletion_delay_minutes)

                                            if not thread_id and force_thread_creation:
                                                thread_name = f"{date_time.strftime('%H:%M - %m/%d')}"
                                                thread = await message.create_thread(name=thread_name)
                                                thread_id = thread.id

                                                if message.role_mentions:
                                                    ping_message = await thread.send(message.role_mentions[0].mention)
                                                    await ping_message.delete()
                                            
                                            elif thread_id:
                                                thread = message.channel.get_thread(thread_id)
                                                new_name = f"{date_time.strftime('%H:%M - %m/%d - ')} {thread.name}"
                                                await thread.edit(name=new_name)

                                        except ValueError:
                                            print("Date format is incorrect, using default unpin time")

                        await bot.schedule_unpin(message, unpin_time)
                        if thread_id:
                            await bot.schedule_thread_deletion(message, thread_id, thread_deletion_time)

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

async def get_unique_role_mentions(message):
    role_mention_ids = re.findall(r'<@&(\d+)>', message.content)

    ordered_role_mentions = []
    for role_id in role_mention_ids:
        for role in message.role_mentions:
            if str(role.id) == role_id:
                ordered_role_mentions.append(role)
                break
    
    return ordered_role_mentions