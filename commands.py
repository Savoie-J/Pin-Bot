import discord
import json

async def setup_commands(bot):
    @bot.tree.command(name="addchannel", description="Add a channel to the monitored list")
    @discord.app_commands.default_permissions(administrator=True)
    @discord.app_commands.describe(channel="The channel to add")
    async def add_channel(interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = interaction.guild.id
        if guild_id not in bot.monitored_channels:
            bot.monitored_channels[guild_id] = []

        if channel.id not in bot.monitored_channels[guild_id]:
            bot.monitored_channels[guild_id].append(channel.id)
            bot.save_monitored_channels()
            await interaction.response.send_message(f"Channel <#{channel.id}> added to the monitored list.", ephemeral=True)
        else:
            await interaction.response.send_message("Channel is already monitored.", ephemeral=True)

    @bot.tree.command(name="removechannel", description="Remove a channel from the monitored list")
    @discord.app_commands.default_permissions(administrator=True)
    @discord.app_commands.describe(channel="The channel to remove")
    async def remove_channel(interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = interaction.guild.id
        if guild_id in bot.monitored_channels and channel.id in bot.monitored_channels[guild_id]:
            bot.monitored_channels[guild_id].remove(channel.id)
            bot.save_monitored_channels()
            await interaction.response.send_message(f"Channel <#{channel.id}> removed from the monitored list.", ephemeral=True)
        else:
            await interaction.response.send_message("Channel is not monitored.", ephemeral=True)

    @bot.tree.command(name="listchannels", description="List all monitored channels")
    async def list_channels(interaction: discord.Interaction):
        guild_id = interaction.guild.id
        if guild_id in bot.monitored_channels:
            channel_mentions = [f"<#{channel_id}>" for channel_id in bot.monitored_channels[guild_id]]
            channels_list = ", ".join(channel_mentions) if channel_mentions else "No channels are currently monitored."
        else:
            channels_list = "No channels are currently monitored."
        await interaction.response.send_message(f"Monitored Channels: {channels_list}", ephemeral=True)

    @bot.tree.command(name="unpintime", description="Set the unpin time (in minutes) for pinned messages")
    @discord.app_commands.default_permissions(administrator=True)
    @discord.app_commands.describe(minutes="The number of minutes, after the group start time, to wait before unpinning")
    async def set_unpin_time(interaction: discord.Interaction, minutes: int):
        guild_id = str(interaction.guild.id)
        if guild_id not in bot.settings:
            bot.settings[guild_id] = {}
        bot.settings[guild_id]['unpin_time'] = minutes
        bot.save_settings()
        await interaction.response.send_message(f"Unpin time set to {minutes} minute(s).", ephemeral=True)

    @bot.tree.command(name="threadtime", description="Set the time (in minutes) before deleting threads")
    @discord.app_commands.default_permissions(administrator=True)
    @discord.app_commands.describe(minutes="The number of minutes, after the group start time, to wait before deleting the thread")
    async def set_thread_deletion_time(interaction: discord.Interaction, minutes: int):
        guild_id = str(interaction.guild.id)
        if guild_id not in bot.settings:
            bot.settings[guild_id] = {}
        bot.settings[guild_id]['thread_deletion_time'] = minutes
        bot.save_settings()
        await interaction.response.send_message(f"Thread deletion time set to {minutes} minute(s).", ephemeral=True)

    @bot.tree.command(name="settings", description="List unpin and thread deletion times from settings.")
    async def list_settings(interaction: discord.Interaction):
        guild_id = interaction.guild.id
        settings = bot.settings.get(str(guild_id), {})

        unpin_time = settings.get('unpin_time', 'Not set')
        thread_deletion_time = settings.get('thread_deletion_time', 'Not set')

        response = (
            f"Unpin Time: {unpin_time} minute(s)\n"
            f"Thread Deletion Time: {thread_deletion_time} minute(s)"
        )
        await interaction.response.send_message(response, ephemeral=True)

    @bot.tree.command(name="webhook_add", description="Add a webhook URL")
    @discord.app_commands.default_permissions(administrator=True)
    @discord.app_commands.describe(url="The webhook URL to add")
    async def webhook_add(interaction: discord.Interaction, url: str):
        guild_id = interaction.guild.id
        webhooks = bot.load_webhooks()

        if guild_id not in webhooks:
            webhooks[guild_id] = []

        if url not in webhooks[guild_id]:
            webhooks[guild_id].append(url)
            bot.save_webhooks(webhooks)
            await interaction.response.send_message(f"Webhook added for this server.", ephemeral=True)
        else:
            await interaction.response.send_message("This webhook URL is already added.", ephemeral=True)

    @bot.tree.command(name="webhook_remove", description="Remove a specific webhook URL for this server")
    @discord.app_commands.default_permissions(administrator=True)
    @discord.app_commands.describe(url="The webhook URL to remove")
    async def webhook_remove(interaction: discord.Interaction, url: str):
        guild_id = interaction.guild.id
        webhooks = bot.load_webhooks()
        
        if guild_id in webhooks and url in webhooks[guild_id]:
            webhooks[guild_id].remove(url)
            if not webhooks[guild_id]:
                del webhooks[guild_id]
            bot.save_webhooks(webhooks)
            await interaction.response.send_message("Webhook removed for this server.", ephemeral=True)
        else:
            await interaction.response.send_message("Webhook not found for this server.", ephemeral=True)

    @bot.tree.command(name="webhook_list", description="List all webhook URLs for this server")
    async def webhook_list(interaction: discord.Interaction):
        guild_id = interaction.guild.id
        webhooks = bot.load_webhooks()
        
        if guild_id in webhooks and webhooks[guild_id]:
            webhook_list = "\n".join(webhooks[guild_id])
            await interaction.response.send_message(f"Webhooks for this server:\n{webhook_list}", ephemeral=True)
        else:
            await interaction.response.send_message("No webhooks found for this server.", ephemeral=True)

    @bot.tree.command(name="invite_add", description="Add a Discord invite link")
    @discord.app_commands.default_permissions(administrator=True)
    @discord.app_commands.describe(invite_link="The Discord invite link to add")
    async def invite_add(interaction: discord.Interaction, invite_link: str):
        guild_id = str(interaction.guild.id)
        
        # Load current settings
        with open('settings.json', 'r') as f:
            settings = json.load(f)
        
        # Initialize guild settings if not present
        if guild_id not in settings:
            settings[guild_id] = {}
        
        # Check if an invite link already exists
        if 'invite_link' in settings[guild_id]:
            await interaction.response.send_message("An invite link already exists for this server. Use /invite_remove to remove it first.", ephemeral=True)
            return
        
        # Add the invite link
        settings[guild_id]['invite_link'] = invite_link
        
        # Save updated settings
        with open('settings.json', 'w') as f:
            json.dump(settings, f, indent=4)
        
        await interaction.response.send_message(f"Invite link added for this server.", ephemeral=True)

    @bot.tree.command(name="invite_remove", description="Remove the Discord invite link")
    @discord.app_commands.default_permissions(administrator=True)
    async def invite_remove(interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        
        # Load current settings
        with open('settings.json', 'r') as f:
            settings = json.load(f)
        
        # Check if an invite link exists
        if guild_id not in settings or 'invite_link' not in settings[guild_id]:
            await interaction.response.send_message("No invite link found for this server.", ephemeral=True)
            return
        
        # Remove the invite link
        del settings[guild_id]['invite_link']
        
        # Save updated settings
        with open('settings.json', 'w') as f:
            json.dump(settings, f, indent=4)
        
        await interaction.response.send_message("Invite link removed for this server.", ephemeral=True)