import os
from pathlib import Path


def int_env(name, default=0):
    value = os.getenv(name, "")
    if not value:
        return default
    return int(value)


DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int_env("GUILD_ID")
VOICE_CHANNEL_ID = int_env("VOICE_CHANNEL_ID")


def default_data_dir():
    explicit_path = os.getenv("NEXOS_DATA_DIR")
    if explicit_path:
        return Path(explicit_path)

    render_disk = Path("/var/data")
    if render_disk.exists():
        return render_disk / "nexos"

    return Path("data")


NEXOS_DATA_DIR = default_data_dir()
