import discord
import json
import datetime
from datetime import datetime
from functions import load_settings

class SettingsView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=300)  # 5 minute timeout
        self.bot = bot
        
    @discord.ui.select(
        placeholder="Select a setting to manage...",
        options=[
            discord.SelectOption(label="Channel Management", value="channels", 
                description="Add or remove monitored channels"),
            discord.SelectOption(label="Timing Settings", value="timing", 
                description="Configure unpin and thread deletion times"),
            discord.SelectOption(label="Thread Settings", value="thread", 
                description="Configure thread creation settings"),
            discord.SelectOption(label="Invite Management", value="invite", 
                description="Manage server invite link"),
            discord.SelectOption(label="Webhook Management", value="webhooks", 
                description="Manage webhook URLs"),
            discord.SelectOption(label="Task Management", value="tasks", 
                description="Manage Tasks"),
        ]
    )
    async def settings_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        if select.values[0] == "channels":
            await interaction.response.send_message(
                view=ChannelManagementView(self.bot),
                ephemeral=True
            )
        elif select.values[0] == "webhooks":
            await interaction.response.send_message(
                view=WebhookManagementView(self.bot),
                ephemeral=True
            )
        elif select.values[0] == "timing":
            await interaction.response.send_message(
                view=TimingSettingsView(self.bot),
                ephemeral=True
            )
        elif select.values[0] == "invite":
            await interaction.response.send_message(
                view=InviteManagementView(self.bot),
                ephemeral=True
            )
        elif select.values[0] == "thread":
            await interaction.response.send_message(
                view=ThreadSettingsView(self.bot),
                ephemeral=True
            )
        elif select.values[0] == "tasks":
            guild_id = interaction.guild.id
            await interaction.response.send_message(
                view=TasksView(self.bot, guild_id),
                ephemeral=True
            )

class ChannelManagementView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=60)
        self.bot = bot

    def get_valid_channels(self, guild):
        """Get list of valid channels in the guild, removing deleted ones."""
        valid_channels = []
        removed_channels = []
        
        if guild.id in self.bot.monitored_channels:
            for channel_id in self.bot.monitored_channels[guild.id]:
                channel = guild.get_channel(channel_id)
                if channel:
                    valid_channels.append(channel)
                else:
                    removed_channels.append(channel_id)
            
            if removed_channels:
                self.bot.monitored_channels[guild.id] = [ch.id for ch in valid_channels]
                self.bot.save_monitored_channels()
                
        return valid_channels

    @discord.ui.button(label="Add Channel", style=discord.ButtonStyle.green)
    async def add_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AddChannelModal(self.bot))

    @discord.ui.button(label="Remove Channel", style=discord.ButtonStyle.red)
    async def remove_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        valid_channels = self.get_valid_channels(interaction.guild)
        
        if not valid_channels:
            await interaction.response.send_message("No channels are currently monitored.", ephemeral=True)
            return

        options = [
            discord.SelectOption(
                label=channel.name,
                value=str(channel.id),
                description=f"#{channel.name}"
            ) for channel in valid_channels
        ]

        view = RemoveChannelView(self.bot, options)
        await interaction.response.send_message("Select a channel to remove:", view=view, ephemeral=True)

    @discord.ui.button(label="List Channels", style=discord.ButtonStyle.blurple)
    async def list_channels(self, interaction: discord.Interaction, button: discord.ui.Button):
        valid_channels = self.get_valid_channels(interaction.guild)
        
        if not valid_channels:
            await interaction.response.send_message("No channels are currently monitored.", ephemeral=True)
            return

        channels_text = " ".join([channel.mention for channel in valid_channels])
        await interaction.response.send_message(f"Monitored Channels: \n{channels_text}", ephemeral=True)

class RemoveChannelView(discord.ui.View):
    def __init__(self, bot, options):
        super().__init__(timeout=60)
        self.bot = bot
        self.add_item(discord.ui.Select(
            placeholder="Select a channel to remove...",
            options=options,
            custom_id="remove_channel_select"
        ))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.data["custom_id"] == "remove_channel_select":
            channel_id = int(interaction.data["values"][0])
            guild_id = interaction.guild.id
            
            if guild_id in self.bot.monitored_channels:
                self.bot.monitored_channels[guild_id].remove(channel_id)
                self.bot.save_monitored_channels()
                
                channel = interaction.guild.get_channel(channel_id)
                channel_text = channel.mention if channel else f"Channel {channel_id}"
                await interaction.response.send_message(
                    f"{channel_text} removed from the monitored channels.",
                    ephemeral=True
                )
            
        return True

class WebhookManagementView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=60)
        self.bot = bot

    @discord.ui.button(label="Add Webhook", style=discord.ButtonStyle.green)
    async def add_webhook(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_id = interaction.guild.id
        webhooks = self.bot.webhooks
        
        if guild_id in webhooks and webhooks[guild_id]:  
            await interaction.response.send_message(
                "⚠ A webhook link already exists for this server. \nPlease remove it before trying to add a new one.",
                ephemeral=True
            )
            return
        
        await interaction.response.send_modal(AddWebhookModal(self.bot))

    @discord.ui.button(label="Remove Webhook", style=discord.ButtonStyle.red)
    async def remove_webhook(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Are you sure you want to remove the webhook link? \nThis action **cannot** be undone.",
            ephemeral=True,
            view=ConfirmRemoveView(self.bot, interaction, 'webhook')
        )

    @discord.ui.button(label="List Webhooks", style=discord.ButtonStyle.blurple)
    async def list_webhooks(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_id = interaction.guild.id
        webhooks = self.bot.webhooks
        
        if guild_id in webhooks and webhooks[guild_id]:
            await interaction.response.send_message(f"🔗 Webhook link for this server:\n{webhooks[guild_id][0]}", ephemeral=True)
        else:
            await interaction.response.send_message("⚠ No webhook link found for this server.", ephemeral=True)

class TimingSettingsView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=60)
        self.bot = bot

    @discord.ui.button(label="Set Unpin Time", style=discord.ButtonStyle.primary)
    async def set_unpin_time(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(UnpinTimeModal(self.bot))

    @discord.ui.button(label="Set Thread Time", style=discord.ButtonStyle.primary)
    async def set_thread_time(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ThreadTimeModal(self.bot))

    @discord.ui.button(label="View Settings", style=discord.ButtonStyle.secondary)
    async def view_settings(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_id = str(interaction.guild.id)
        settings = self.bot.settings.get(guild_id, {})

        unpin_time = settings.get('unpin_time', '60')
        thread_deletion_time = settings.get('thread_deletion_time', '60')

        response = (
            f"Unpin Time: `{unpin_time} minute(s)`\n"
            f"Thread Deletion Time: `{thread_deletion_time} minute(s)`"
        )
        await interaction.response.send_message(response, ephemeral=True)

class InviteManagementView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=60)
        self.bot = bot

    @discord.ui.button(label="Set Invite Link", style=discord.ButtonStyle.green)
    async def set_invite(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_id = str(interaction.guild.id)
        settings = load_settings("settings.json")

        if guild_id in settings and "invite_link" in settings[guild_id]:  
            await interaction.response.send_message(
                "⚠ An invite link already exists for this server. \nRemove it before trying to add a new one.",
                ephemeral=True
            )
            return

        await interaction.response.send_modal(InviteLinkModal(self.bot))

    @discord.ui.button(label="Remove Invite Link", style=discord.ButtonStyle.red)
    async def remove_invite(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Are you sure you want to remove the invite link? \nThis action **cannot** be undone.",
            ephemeral=True,
            view=ConfirmRemoveView(self.bot, interaction, 'invite')
        )

    @discord.ui.button(label="View Invite Link", style=discord.ButtonStyle.blurple)
    async def view_invite(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_id = str(interaction.guild.id)
        settings = load_settings("settings.json")

        if guild_id in settings and "invite_link" in settings[guild_id]:
            await interaction.response.send_message(f"🔗 Invite link for this server: \n{settings[guild_id]['invite_link']}", ephemeral=True)
        else:
            await interaction.response.send_message("⚠ No invite link set.", ephemeral=True)

class ThreadSettingsView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=60)
        self.bot = bot

    @discord.ui.button(label="Enable Threads", style=discord.ButtonStyle.green)
    async def enable_threads(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_thread_mode(interaction, True)

    @discord.ui.button(label="Disable Threads", style=discord.ButtonStyle.red)
    async def disable_threads(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_thread_mode(interaction, False)

    @discord.ui.button(label="View Status", style=discord.ButtonStyle.blurple)
    async def view_status(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_id = str(interaction.guild.id)
        
        with open('settings.json', 'r') as f:
            settings = json.load(f)
        
        if guild_id not in settings or 'force_thread_creation' not in settings[guild_id]:
            await interaction.response.send_message(
                "Thread creation mode is not set for this server. Default: `False`",
                ephemeral=True
            )
            return
        
        enabled = settings[guild_id]['force_thread_creation']
        await interaction.response.send_message(
            f"Thread creation mode is currently: `{enabled}`",
            ephemeral=True
        )

    async def update_thread_mode(self, interaction: discord.Interaction, enabled: bool):
        guild_id = str(interaction.guild.id)
        
        with open('settings.json', 'r') as f:
            settings = json.load(f)
        
        if guild_id not in settings:
            settings[guild_id] = {}
        
        settings[guild_id]['force_thread_creation'] = enabled
        
        with open('settings.json', 'w') as f:
            json.dump(settings, f, indent=4)
        
        await interaction.response.send_message(
            f"Thread creation mode has been set to: `{enabled}`",
            ephemeral=True
        )

class TasksView(discord.ui.View):
    def __init__(self, bot, guild_id):
        super().__init__(timeout=60)
        self.guild_id = str(guild_id)
        self.bot = bot

    @discord.ui.button(label="Delete Unpin Task", style=discord.ButtonStyle.red)
    async def delete_unpin_task(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.guild_id not in self.bot.tasks:
            await interaction.response.send_message("No tasks found for this server.", ephemeral=True)
            return

        unpin_tasks = [task for task in self.bot.tasks[self.guild_id] if task['type'] == 'unpin']

        if not unpin_tasks:
            await interaction.response.send_message("No unpin tasks found for this server.", ephemeral=True)
            return

        unique_unpin_tasks = []
        seen_message_ids = set()
        for task in unpin_tasks:
            if task['message_id'] not in seen_message_ids:
                unique_unpin_tasks.append(task)
                seen_message_ids.add(task['message_id'])

        options = []
        for task in unique_unpin_tasks:
            try:
                channel = interaction.guild.get_channel(task['channel_id'])

                unpin_time = task['unpin_time']
                if isinstance(unpin_time, str):
                    formatted_time = datetime.fromisoformat(unpin_time).strftime('%H:%M %m-%d-%Y')
                else:
                    formatted_time = str(unpin_time)

                label = f"Channel: {channel.name if channel else '(Deleted)'} | Time: {formatted_time}"
                description = f"Message ID: {task['message_id']}"

                value = f"unpin_{task['channel_id']}_{task['message_id']}"

                options.append(
                    discord.SelectOption(
                        label=label[:100],
                        description=description[:100],
                        value=value
                    )
                )
            except Exception as e:
                print(f"Error processing unpin task: {task}. Error: {e}")
                continue

        if not options:
            await interaction.response.send_message("No valid unpin tasks found for this server.", ephemeral=True)
            return

        view = discord.ui.View()
        select = discord.ui.Select(
            placeholder="Select an unpin task to delete...",
            options=options,
            custom_id="remove_unpin_task_select"
        )
        view.add_item(select)

        async def select_callback(interaction: discord.Interaction):
            selected_value = interaction.data["values"][0]
            #print(selected_value)
            parts = selected_value.split("_")
            #print(parts)
            if len(parts) != 3:
                await interaction.response.send_message("Invalid task selection.", ephemeral=True)
                return

            task_type, selected_channel_id, selected_message_id = parts

            if task_type != "unpin":
                await interaction.response.send_message("Invalid task type.", ephemeral=True)
                return

            # Remove all tasks with the selected message_id
            self.bot.tasks[self.guild_id] = [
                task for task in self.bot.tasks[self.guild_id]
                if task['type'] != 'unpin' or
                task['message_id'] != int(selected_message_id)
            ]

            if not self.bot.tasks[self.guild_id]:
                del self.bot.tasks[self.guild_id]

            self.bot.save_tasks()
            await interaction.response.send_message("Deleted the selected unpin task.", ephemeral=True)

        select.callback = select_callback
        await interaction.response.send_message("Select an unpin task to delete:", view=view, ephemeral=True)

    @discord.ui.button(label="Delete Thread Task", style=discord.ButtonStyle.red)
    async def delete_thread_task(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.guild_id not in self.bot.tasks:
            await interaction.response.send_message("No tasks found for this server.", ephemeral=True)
            return

        thread_tasks = [task for task in self.bot.tasks[self.guild_id] if task['type'] == 'thread_deletion']

        if not thread_tasks:
            await interaction.response.send_message("No thread deletion tasks found for this server.", ephemeral=True)
            return

        unique_thread_tasks = []
        seen_thread_ids = set()
        for task in thread_tasks:
            if task['thread_id'] not in seen_thread_ids:
                unique_thread_tasks.append(task)
                seen_thread_ids.add(task['thread_id'])

        options = []
        for task in unique_thread_tasks:
            try:
                channel = interaction.guild.get_channel(task['channel_id'])

                thread_deletion_time = task['thread_deletion_time']
                if isinstance(thread_deletion_time, str):
                    formatted_time = datetime.fromisoformat(thread_deletion_time).strftime('%H:%M %m-%d-%Y')
                else:
                    formatted_time = str(thread_deletion_time)

                label = f"Channel: {channel.name if channel else '(Deleted)'} | Time: {formatted_time}"
                description = f"Thread ID: {task['thread_id']}"

                value = f"thread-deletion_{task['channel_id']}_{task['thread_id']}"
                #print(f"SelectOption value: {value}") 
                options.append(
                    discord.SelectOption(
                        label=label[:100],
                        description=description[:100],
                        value=value
                    )
                )
            except Exception as e:
                print(f"Error processing thread task: {task}. Error: {e}")
                continue

        if not options:
            await interaction.response.send_message("No valid thread deletion tasks found for this server.", ephemeral=True)
            return

        view = discord.ui.View()
        select = discord.ui.Select(
            placeholder="Select a thread task to delete...",
            options=options,
            custom_id="remove_thread_task_select"
        )
        view.add_item(select)

        async def select_callback(interaction: discord.Interaction):
            selected_value = interaction.data["values"][0]
            #print(f"Selected value: {selected_value}")  # Debug print
            parts = selected_value.split("_")
            #print(parts)
            #print(len(parts))
            # Ensure there are exactly 3 parts
            if len(parts) != 3:
                await interaction.response.send_message("Invalid task selection.", ephemeral=True)
                return

            task_type, selected_channel_id, selected_thread_id = parts

            #print(task_type)
            # Ensure the task type is correct
            if task_type != "thread-deletion":
                await interaction.response.send_message("Invalid task type.", ephemeral=True)
                return

            # Convert selected_thread_id to integer for comparison
            selected_thread_id = int(selected_thread_id)

            # Debug: Print tasks before deletion
            #print(f"Tasks before deletion: {self.bot.tasks[self.guild_id]}")

            # Remove all tasks with the selected thread_id
            self.bot.tasks[self.guild_id] = [
                task for task in self.bot.tasks[self.guild_id]
                if task['type'] != 'thread_deletion' or
                int(task['thread_id']) != selected_thread_id
            ]

            # Debug: Print tasks after deletion
            #print(f"Tasks after deletion: {self.bot.tasks[self.guild_id]}")

            if not self.bot.tasks[self.guild_id]:
                del self.bot.tasks[self.guild_id]

            self.bot.save_tasks()
            await interaction.response.send_message("Deleted the selected thread task.", ephemeral=True)

        select.callback = select_callback
        await interaction.response.send_message("Select a thread task to delete:", view=view, ephemeral=True)

    @discord.ui.button(label="List Tasks", style=discord.ButtonStyle.blurple)
    async def list_tasks(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.guild_id not in self.bot.tasks:
            await interaction.response.send_message("No tasks scheduled for this server.", ephemeral=True)
            return

        unpin_tasks = []
        thread_tasks = []

        for task in self.bot.tasks[self.guild_id]:
            try:
                if task['type'] == 'unpin':
                    unpin_time = task['unpin_time']
                    if isinstance(unpin_time, str):
                        formatted_time = datetime.fromisoformat(unpin_time).strftime("%H:%M | %m-%d-%Y")
                    else:
                        formatted_time = str(unpin_time)

                    message_link = f"https://discord.com/channels/{self.guild_id}/{task['channel_id']}/{task['message_id']}"
                    unpin_tasks.append(f"<#{task['channel_id']}> - {formatted_time}\n└ [Jump to Message]({message_link})")

                elif task['type'] == 'thread_deletion':
                    thread_deletion_time = task['thread_deletion_time']
                    if isinstance(thread_deletion_time, str):
                        formatted_time = datetime.fromisoformat(thread_deletion_time).strftime("%H:%M | %m-%d-%Y")
                    else:
                        formatted_time = str(thread_deletion_time)

                    thread_link = f"https://discord.com/channels/{self.guild_id}/{task['channel_id']}/{task['thread_id']}"
                    thread_tasks.append(f"<#{task['channel_id']}> - {formatted_time}\n└ [Jump to Thread]({thread_link})")
            except Exception as e:
                print(f"Error processing task: {task}. Error: {e}")
                continue

        task_message = ""

        if unpin_tasks:
            task_message += "**Unpin Tasks:**\n" + "\n\n".join(unpin_tasks) + "\n\n"

        if thread_tasks:
            task_message += "**Thread Deletion Tasks:**\n" + "\n\n".join(thread_tasks)

        if not task_message:
            task_message = "No tasks scheduled."

        # Send the initial response
        await interaction.response.send_message("Fetching tasks...", ephemeral=True)

        # Split the message into chunks if it exceeds 2000 characters
        if len(task_message) > 2000:
            chunks = [task_message[i:i + 2000] for i in range(0, len(task_message), 2000)]
            for chunk in chunks:
                await interaction.followup.send(chunk, ephemeral=True)
        else:
            await interaction.followup.send(task_message, ephemeral=True)

class ConfirmRemoveView(discord.ui.View):
    def __init__(self, bot, interaction, action_type):
        super().__init__(timeout=60) 
        self.bot = bot
        self.interaction = interaction
        self.action_type = action_type  
        
    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_id = str(self.interaction.guild.id) 
        
        if self.action_type == 'invite':
            with open('settings.json', 'r') as f:
                settings = json.load(f)
            
            if guild_id not in settings or 'invite_link' not in settings[guild_id]:
                await interaction.response.send_message("⚠ No invite link found for this server.", ephemeral=True)
                return
            
            del settings[guild_id]['invite_link']
            
            with open('settings.json', 'w') as f:
                json.dump(settings, f, indent=4)
            
            await interaction.response.send_message("🔗 Invite link removed for this server.", ephemeral=True)
        
        elif self.action_type == 'webhook':
            webhooks = self.bot.webhooks
            guild_id = self.interaction.guild.id
            
            if guild_id not in webhooks or not webhooks[guild_id]:
                await interaction.response.send_message("⚠ No webhook link found for this server.", ephemeral=True)
                return
            
            del webhooks[guild_id]
            self.bot.save_webhooks(webhooks)
            
            await interaction.response.send_message("🔗 Webhook link removed for this server.", ephemeral=True)

        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"{self.action_type.capitalize()} link removal canceled.", ephemeral=True)
        
        self.stop()

class AddChannelModal(discord.ui.Modal, title="Add Channel"):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.channel_input = discord.ui.TextInput(
            label="Channel ID",
            placeholder="Enter the channel's ID...",
            required=True,
            min_length=1,
            max_length=20
        )
        self.add_item(self.channel_input)

    async def on_submit(self, interaction: discord.Interaction):
        input_value = self.channel_input.value.strip()
        
        if not input_value.isdigit():
            await interaction.response.send_message("Invalid channel ID. Please enter a numeric ID.", ephemeral=True)
            return

        channel = interaction.guild.get_channel(int(input_value))
        
        if not channel or not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message("Channel not found. Please enter a valid text channel ID.", ephemeral=True)
            return

        await self.add_channel(interaction, channel)

    async def add_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = interaction.guild.id

        if guild_id not in self.bot.monitored_channels:
            self.bot.monitored_channels[guild_id] = []

        if channel.id in self.bot.monitored_channels[guild_id]:
            await interaction.response.send_message(
                f"Channel {channel.mention} is already being monitored.",
                ephemeral=True
            )
            return

        self.bot.monitored_channels[guild_id].append(channel.id)
        self.bot.save_monitored_channels()
        await interaction.response.send_message(
            f"Added {channel.mention} to the monitored channels.",
            ephemeral=True
        )

class AddWebhookModal(discord.ui.Modal, title="Add Webhook"):
    webhook_url = discord.ui.TextInput(
        label="Webhook URL",
        placeholder="Enter the webhook's URL",
        required=True
    )

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        webhooks = self.bot.webhooks

        if guild_id not in webhooks:
            webhooks[guild_id] = []

        if self.webhook_url.value not in webhooks[guild_id]:
            webhooks[guild_id].append(self.webhook_url.value)
            self.bot.save_webhooks(webhooks)
            await interaction.response.send_message("Webhook added for this server.", ephemeral=True)
        else:
            await interaction.response.send_message("This webhook URL is already added.", ephemeral=True)

class UnpinTimeModal(discord.ui.Modal, title="Set Unpin Time"):
    minutes = discord.ui.TextInput(
        label="Minutes",
        placeholder="Enter the number of minutes",
        required=True
    )

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        try:
            minutes = int(self.minutes.value)
            guild_id = str(interaction.guild.id)
            
            if guild_id not in self.bot.settings:
                self.bot.settings[guild_id] = {}
            
            self.bot.settings[guild_id]['unpin_time'] = minutes
            self.bot.save_settings()
            await interaction.response.send_message(f"Unpin time set to `{minutes} minute(s)`.", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("Please enter a valid number.", ephemeral=True)

class ThreadTimeModal(discord.ui.Modal, title="Set Thread Deletion Time"):
    minutes = discord.ui.TextInput(
        label="Minutes",
        placeholder="Enter the number of minutes",
        required=True
    )

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        try:
            minutes = int(self.minutes.value)
            guild_id = str(interaction.guild.id)
            
            if guild_id not in self.bot.settings:
                self.bot.settings[guild_id] = {}
            
            self.bot.settings[guild_id]['thread_deletion_time'] = minutes
            self.bot.save_settings()
            await interaction.response.send_message(f"Thread deletion time set to `{minutes} minute(s)`.", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("Please enter a valid number.", ephemeral=True)

class InviteLinkModal(discord.ui.Modal, title="Set Invite Link"):
    invite_link = discord.ui.TextInput(
        label="Invite Link",
        placeholder="Enter the Discord invite link",
        required=True
    )

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        
        with open('settings.json', 'r') as f:
            settings = json.load(f)
        
        if guild_id not in settings:
            settings[guild_id] = {}
        
        settings[guild_id]['invite_link'] = self.invite_link.value
        
        with open('settings.json', 'w') as f:
            json.dump(settings, f, indent=4)
        
        await interaction.response.send_message("Invite link added for this server.", ephemeral=True) 