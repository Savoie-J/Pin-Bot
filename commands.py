import discord
import views
from logic import handle_message
from functions import load_settings, load_webhooks, load_monitored_channels

async def setup_commands(bot):
    @bot.tree.command(name="settings", description="List unpin and thread deletion times from settings.")
    async def list_settings(interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        
        settings = load_settings('settings.json')
        webhooks = load_webhooks('webhooks.json')
        monitored_channels = load_monitored_channels('monitored_channels.json')
        
        guild_settings = settings.get(guild_id, {})
        unpin_time = guild_settings.get('unpin_time', '60')
        thread_deletion_time = guild_settings.get('thread_deletion_time', '60')
        force_thread_creation = guild_settings.get('force_thread_creation', 'False')
        invite_link = guild_settings.get('invite_link', 'Not set')
        webhook_link = webhooks.get(int(guild_id), ['Not set'])[0] if int(guild_id) in webhooks else 'Not set'
        
        channels = monitored_channels.get(int(guild_id), [])
        if channels:
            channel_triples = [f"<#{channels[i]}> <#{channels[i+1]}> <#{channels[i+2]}>" if i+2 < len(channels) else f"<#{channels[i]}>" for i in range(0, len(channels), 3)]
            monitored_channels_list = "\n".join(channel_triples)
        else:
            monitored_channels_list = "No monitored channels set."

        embed = discord.Embed(
            title=f"{interaction.guild.name} Settings",
            color=discord.Color.random()
        )
        
        embed.add_field(name="Unpin Time", value=f"`{unpin_time} minute(s)`", inline=False)
        embed.add_field(name="Thread Deletion Time", value=f"`{thread_deletion_time} minute(s)`", inline=False)
        embed.add_field(name="Thread Creation Enabled", value=f"`{force_thread_creation}`", inline=False)
        embed.add_field(name="Discord Invite Link", value=f"`{invite_link}`", inline=False)
        embed.add_field(name="Webhook Link", value=f"`{webhook_link}`", inline=False)
        embed.add_field(name="Monitored Channels", value=monitored_channels_list, inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @bot.tree.command(name="settings-panel", description="Manage bot settings")
    @discord.app_commands.default_permissions(administrator=True)
    async def settings_panel(interaction: discord.Interaction):
        view = views.SettingsView(interaction.client)
        await interaction.response.send_message("Select a setting to manage:", view=view, ephemeral=True)

    @bot.tree.context_menu(name="Process Message")
    async def pin_context_menu(interaction: discord.Interaction, message: discord.Message):
        await interaction.response.defer(ephemeral=True)

        try:
            guild_id = message.guild.id
            if (guild_id in bot.monitored_channels and 
                message.channel.id in bot.monitored_channels[guild_id] and 
                message.author.id in [457573832350236672, 735842992002433084, 
                                    1284787241943699486, 1286639371038232698]):
                
                await handle_message(bot, message)
                await interaction.followup.send("Message processed successfully!", ephemeral=True)
            else:
                await interaction.followup.send(
                    "Please ensure the message is in a monitored channel, by a valid author.", 
                    ephemeral=True
                )

        except Exception as e:
            print(f"Error in Pin Message context menu: {e}")
            await interaction.followup.send(
                "An error occurred while processing the message.", 
                ephemeral=True
            )