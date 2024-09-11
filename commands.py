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
            print(f"Adding channel {channel.id} to monitored list.")
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