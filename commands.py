import discord

async def setup_commands(bot):
    @bot.tree.command(name="addchannel", description="Add a channel to the monitored list")
    @discord.app_commands.default_permissions(administrator=True)
    @discord.app_commands.describe(channel="The channel to add")
    async def add_channel(interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = interaction.guild.id
        if guild_id not in bot.monitored_channels:
            bot.monitored_channels[guild_id] = []

        if channel.id not in bot.monitored_channels[guild_id]:
            #print(f"Adding channel {channel.id} to monitored list.")
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
        guild_id = str(interaction.guild.id)  # Ensure guild_id is a string
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