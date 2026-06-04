import os


def int_env(name, default=0):
    value = os.getenv(name, "")
    if not value:
        return default
    return int(value)


DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int_env("GUILD_ID")
VOICE_CHANNEL_ID = int_env("VOICE_CHANNEL_ID")
