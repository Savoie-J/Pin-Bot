import json

def load_monitored_channels(data_file):
    try:
        with open(data_file, 'r') as f:
            monitored_channels = json.load(f)
            monitored_channels = {int(guild_id): [int(channel_id) for channel_id in channels]
                                  for guild_id, channels in monitored_channels.items()}
            print("Loaded monitored channels from file:", monitored_channels)
            return monitored_channels
    except (FileNotFoundError, json.JSONDecodeError):
        print("No saved monitored channels file found or error decoding JSON, starting fresh.")
        return {}

def save_monitored_channels(monitored_channels, data_file):
    try:
        with open(data_file, 'w') as f:
            json.dump({str(k): [str(ch) for ch in v] for k, v in monitored_channels.items()}, f, indent=4)
            print("Saved monitored channels to file:", monitored_channels)
    except Exception as e:
        print(f"Failed to save monitored channels: {e}")