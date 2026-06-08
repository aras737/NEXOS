import datetime

import discord

from core.config import LOG_CHANNEL_ID
from core.embeds import make_embed
from core.emojis import with_emoji
from core.storage import append_log, get_guild_setting, set_guild_setting, update_last_action


LOG_TYPE_LABELS = {
    "general": "Genel Log",
    "message": "Mesaj Log",
    "voice": "Ses Log",
    "mod": "Mod Log",
    "member": "Giris-Cikis Log",
    "punishment": "Ceza Log"
}

LOG_TYPE_ALIASES = {
    "general": ["log", "genel-log", "bot-log", "sistem-log"],
    "message": ["mesaj-log", "message-log", "chat-log", "sohbet-log"],
    "voice": ["ses-log", "voice-log", "sesli-log"],
    "mod": ["mod-log", "moderasyon-log", "moderation-log", "yonetim-log"],
    "member": ["giris-cikis-log", "giris-cikis", "welcome-log", "uye-log", "member-log"],
    "punishment": ["ceza-log", "punishment-log", "ban-log", "warn-log", "uyari-log"]
}

TURKISH_TRANSLATION = str.maketrans({
    "ç": "c",
    "ğ": "g",
    "ı": "i",
    "ö": "o",
    "ş": "s",
    "ü": "u",
    "İ": "i",
    "Ç": "c",
    "Ğ": "g",
    "Ö": "o",
    "Ş": "s",
    "Ü": "u"
})


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc)


def trim(value, limit=1024):
    text = str(value)
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def normalize_text(value):
    text = str(value or "").translate(TURKISH_TRANSLATION).lower()
    cleaned = "".join(char if char.isalnum() else "-" for char in text)
    return "-".join(part for part in cleaned.split("-") if part)


def valid_log_type(log_type):
    return log_type if log_type in LOG_TYPE_LABELS else "general"


def log_type_label(log_type):
    return LOG_TYPE_LABELS.get(valid_log_type(log_type), LOG_TYPE_LABELS["general"])


def infer_log_type(title):
    normalized = normalize_text(title)

    if any(item in normalized for item in ["mesaj", "message"]):
        return "message"
    if any(item in normalized for item in ["ses", "voice", "sese", "sesten"]):
        return "voice"
    if any(item in normalized for item in ["ban", "timeout", "sustur", "warn", "uyari", "kick", "ceza", "unban"]):
        return "punishment"
    if any(item in normalized for item in ["uye-katildi", "uye-ayrildi", "giris-cikis", "hos-geldin", "galaksi-cikisi"]):
        return "member"
    if any(item in normalized for item in [
        "moderasyon",
        "rol",
        "kanal",
        "ticket",
        "cekilis",
        "giveaway",
        "lock",
        "unlock",
        "slowmode",
        "oto-rol",
        "buton-rol",
        "emoji"
    ]):
        return "mod"
    return "general"


def log_channels_setting(guild):
    if not guild:
        return {}
    channels = get_guild_setting(guild.id, "log_channels", {})
    return channels if isinstance(channels, dict) else {}


def set_log_channel_setting(guild_id, log_type, channel_id):
    log_type = valid_log_type(log_type)
    channels = get_guild_setting(guild_id, "log_channels", {})
    if not isinstance(channels, dict):
        channels = {}
    channels[log_type] = int(channel_id)
    set_guild_setting(guild_id, "log_channels", channels)

    if log_type == "general":
        set_guild_setting(guild_id, "log_channel_id", int(channel_id))


def log_channel_id(guild, log_type="general"):
    if not guild:
        return None

    log_type = valid_log_type(log_type)
    channels = log_channels_setting(guild)
    stored = channels.get(log_type)
    if stored:
        return stored

    if log_type == "general":
        stored = get_guild_setting(guild.id, "log_channel_id")
        return stored or LOG_CHANNEL_ID

    return None


def find_named_log_channel(guild, log_type):
    aliases = set(LOG_TYPE_ALIASES.get(valid_log_type(log_type), []))
    for channel in guild.text_channels:
        if normalize_text(channel.name) in aliases:
            return channel
    return None


async def fetch_channel(guild, channel_id):
    if not guild or not channel_id:
        return None

    try:
        channel_id = int(channel_id)
    except (TypeError, ValueError):
        return None

    channel = guild.get_channel(channel_id)
    if channel:
        return channel

    try:
        return await guild.fetch_channel(channel_id)
    except Exception:
        return None


async def get_log_channel(guild, log_type="general"):
    if not guild:
        return None

    log_type = valid_log_type(log_type)
    channel = await fetch_channel(guild, log_channel_id(guild, log_type))
    if channel:
        return channel

    named_channel = find_named_log_channel(guild, log_type)
    if named_channel:
        return named_channel

    if log_type != "general":
        return await get_log_channel(guild, "general")

    return None


async def log_event(guild, title, description, color=0x5865F2, fields=None, log_type=None):
    fields = fields or []
    resolved_type = valid_log_type(log_type or infer_log_type(title))
    event = {
        "created_at": utc_now().isoformat(),
        "guild_id": guild.id if guild else None,
        "type": resolved_type,
        "type_label": log_type_label(resolved_type),
        "title": title,
        "description": description,
        "fields": [{"name": name, "value": str(value)} for name, value in fields]
    }
    append_log(event)
    update_last_action(event["guild_id"], resolved_type, event)

    channel = await get_log_channel(guild, resolved_type)
    if not channel:
        return False

    embed = make_embed(title, description, color)
    embed.timestamp = utc_now()
    embed.set_footer(text=f"NEXOS {log_type_label(resolved_type)}")
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
    if command == "last-actions":
        return

    channel = interaction.channel or interaction.channel_id
    await log_event(
        interaction.guild,
        with_emoji("settings", "Komut Kullanildi"),
        f"/{command}",
        0x3498DB,
        [
            ("Kullanan", f"{interaction.user} ({interaction.user.id})"),
            ("Kanal", f"{channel} ({interaction.channel_id})"),
            ("Secenekler", interaction_options(interaction.data))
        ],
        log_type="general"
    )
