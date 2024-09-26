import json

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