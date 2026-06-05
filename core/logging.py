import datetime

import discord

from core.config import LOG_CHANNEL_ID
from core.embeds import make_embed
from core.storage import append_log, get_guild_setting


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc)


def trim(value, limit=1024):
    text = str(value)
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def log_channel_id(guild):
    stored = get_guild_setting(guild.id, "log_channel_id") if guild else None
    return stored or LOG_CHANNEL_ID


async def get_log_channel(guild):
    channel_id = log_channel_id(guild)
    if not guild or not channel_id:
        return None

    channel = guild.get_channel(int(channel_id))
    if channel:
        return channel

    try:
        return await guild.fetch_channel(int(channel_id))
    except Exception:
        return None


async def log_event(guild, title, description, color=0x5865F2, fields=None):
    fields = fields or []
    event = {
        "created_at": utc_now().isoformat(),
        "guild_id": guild.id if guild else None,
        "title": title,
        "description": description,
        "fields": [{"name": name, "value": str(value)} for name, value in fields]
    }
    append_log(event)

    channel = await get_log_channel(guild)
    if not channel:
        return False

    embed = make_embed(title, description, color)
    embed.timestamp = utc_now()
    for name, value in fields:
        embed.add_field(name=name, value=trim(value), inline=False)

    try:
        await channel.send(embed=embed)
        return True
    except discord.HTTPException:
        return False


def interaction_options(data):
    options = data.get("options", [])
    if not options:
        return "Yok"

    lines = []

    def walk(items, prefix=""):
        for item in items:
            name = item.get("name", "bilinmiyor")
            full_name = f"{prefix}.{name}" if prefix else name
            if "value" in item:
                lines.append(f"{full_name}: {item['value']}")
            if item.get("options"):
                walk(item["options"], full_name)

    walk(options)
    return "\n".join(lines) if lines else "Yok"


async def log_interaction(interaction):
    if not interaction.guild or interaction.type is not discord.InteractionType.application_command:
        return

    command = interaction.data.get("name", "bilinmiyor")
    channel = interaction.channel or interaction.channel_id
    await log_event(
        interaction.guild,
        "Komut Kullanildi",
        f"/{command}",
        0x3498DB,
        [
            ("Kullanan", f"{interaction.user} ({interaction.user.id})"),
            ("Kanal", f"{channel} ({interaction.channel_id})"),
            ("Secenekler", interaction_options(interaction.data))
        ]
    )
