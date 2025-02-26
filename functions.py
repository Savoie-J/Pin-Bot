import json
from datetime import datetime, timezone

def load_monitored_channels(data_file):
    try:
        with open(data_file, 'r') as f:
            monitored_channels = json.load(f)
            monitored_channels = {int(guild_id): [int(channel_id) for channel_id in channels]
                                  for guild_id, channels in monitored_channels.items()}
            return monitored_channels
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading monitored channels file: {e}. Starting fresh.")
        save_monitored_channels({}, data_file)
        return {}

def save_monitored_channels(monitored_channels, data_file):
    try:
        with open(data_file, 'w') as f:
            json.dump({str(k): [str(ch) for ch in v] for k, v in monitored_channels.items()}, f, indent=4)
    except Exception as e:
        print(f"Failed to save monitored channels: {e}")

def load_settings(settings_file):
    try:
        with open(settings_file, "r") as file:
            settings = json.load(file)
            return settings
    except FileNotFoundError:
        print(f"No settings file found at {settings_file}, starting fresh.")
        save_settings({}, settings_file)
        return {}

def save_settings(settings, settings_file):
    try:
        with open(settings_file, "w") as file:
            json.dump(settings, file, indent=4)
    except Exception as e:
        print(f"Failed to save settings: {e}")

def load_webhooks(webhooks_file):
    try:
        with open(webhooks_file, 'r') as file:
            webhooks = json.load(file)
            webhooks = {int(guild_id): urls for guild_id, urls in webhooks.items()}
            return webhooks
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"No webhooks file found at {webhooks_file}, starting fresh.")
        save_webhooks({}, webhooks_file)
        return {}

def save_webhooks(webhooks, webhooks_file):
    try:
        with open(webhooks_file, 'w') as f:
            json.dump({str(k): v for k, v in webhooks.items()}, f, indent=4)
    except Exception as e:
        print(f"Failed to save webhooks: {e}")

def load_tasks(tasks_file):
    try:
        with open(tasks_file, 'r') as file:
            tasks = json.load(file)
            # Convert string timestamps back to datetime objects
            for guild_id, guild_tasks in tasks.items():
                for task in guild_tasks:
                    if 'unpin_time' in task:
                        task['unpin_time'] = datetime.fromisoformat(task['unpin_time'])
                    if 'thread_deletion_time' in task:
                        task['thread_deletion_time'] = datetime.fromisoformat(task['thread_deletion_time'])
            return tasks
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"No tasks file found at {tasks_file}, starting fresh.")
        save_tasks({}, tasks_file)
        return {}

def save_tasks(tasks, tasks_file):
    try:
        # Convert datetime objects to ISO format strings for JSON serialization
        serializable_tasks = {}
        for guild_id, guild_tasks in tasks.items():
            guild_id_str = str(guild_id)  # Ensure guild_id is a string
            serializable_tasks[guild_id_str] = []
            for task in guild_tasks:
                serializable_task = task.copy()
                if 'unpin_time' in serializable_task:
                    serializable_task['unpin_time'] = serializable_task['unpin_time'].isoformat()
                if 'thread_deletion_time' in serializable_task:
                    serializable_task['thread_deletion_time'] = serializable_task['thread_deletion_time'].isoformat()
                serializable_tasks[guild_id_str].append(serializable_task)

        # Remove any empty guild entries
        serializable_tasks = {k: v for k, v in serializable_tasks.items() if v}

        with open(tasks_file, 'w') as f:
            json.dump(serializable_tasks, f, indent=4)
    except Exception as e:
        print(f"Failed to save tasks: {e}")

async def add_unpin_task(tasks, guild_id, channel_id, message_id, unpin_time):
    guild_id_str = str(guild_id)
    if guild_id_str not in tasks:
        tasks[guild_id_str] = []
    
    tasks[guild_id_str].append({
        'type': 'unpin',
        'channel_id': channel_id,
        'message_id': message_id,
        'unpin_time': unpin_time,
        'retries': 0
    })

async def add_thread_deletion_task(tasks, guild_id, channel_id, thread_id, thread_deletion_time):
    guild_id_str = str(guild_id)
    if guild_id_str not in tasks:
        tasks[guild_id_str] = []
    
    tasks[guild_id_str].append({
        'type': 'thread_deletion',
        'channel_id': channel_id,
        'thread_id': thread_id,
        'thread_deletion_time': thread_deletion_time,
        'retries': 0
    })

async def remove_completed_tasks(tasks, guild_id):
    now = datetime.now(timezone.utc)
    
    if guild_id not in tasks:
        return

    tasks[guild_id] = [task for task in tasks[guild_id] 
                      if ('unpin_time' in task and task['unpin_time'] > now) or 
                         ('thread_deletion_time' in task and task['thread_deletion_time'] > now)]
    
    if guild_id in tasks and not tasks[guild_id]:
        print(f"All tasks completed for guild {guild_id}, removing from tasks.")
        del tasks[guild_id]

async def get_due_tasks(tasks):
    now = datetime.now(timezone.utc)
    due_tasks = [(guild_id, task) for guild_id, guild_tasks in tasks.items() for task in guild_tasks 
                 if ('unpin_time' in task and task['unpin_time'] <= now) or 
                    ('thread_deletion_time' in task and task['thread_deletion_time'] <= now)]
    return due_tasks