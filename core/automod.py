import datetime
import re
import time

import discord

from core.emojis import with_emoji
from core.logging import log_event, normalize_text, trim
from core.storage import add_warning, get_guild_setting, set_guild_setting


INVITE_RE = re.compile(r"(discord\.gg/|discord(?:app)?\.com/invite/)", re.IGNORECASE)
LINK_RE = re.compile(r"(https?://|www\.)", re.IGNORECASE)
SPAM_BUCKETS = {}
VALID_ACTIONS = {"delete", "warn", "timeout"}


def automod_enabled(guild_id):
    return get_guild_setting(guild_id, "automod_enabled", True) is not False


def automod_setting(guild_id, key, default):
    return get_guild_setting(guild_id, f"automod_{key}", default)


def automod_words(guild_id):
    words = get_guild_setting(guild_id, "automod_banned_words", [])
    if not isinstance(words, list):
        return []
    return [normalize_text(word) for word in words if str(word).strip()]


def add_banned_word(guild_id, word):
    words = get_guild_setting(guild_id, "automod_banned_words", [])
    if not isinstance(words, list):
        words = []
    clean = normalize_text(word)
    if clean and clean not in [normalize_text(item) for item in words]:
        words.append(str(word).strip())
    set_guild_setting(guild_id, "automod_banned_words", words)
    return words


def remove_banned_word(guild_id, word):
    clean = normalize_text(word)
    words = get_guild_setting(guild_id, "automod_banned_words", [])
    if not isinstance(words, list):
        words = []
    words = [item for item in words if normalize_text(item) != clean]
    set_guild_setting(guild_id, "automod_banned_words", words)
    return words


def can_bypass_automod(member):
    perms = getattr(member, "guild_permissions", None)
    return bool(perms and (perms.administrator or perms.manage_messages or perms.moderate_members))


def spam_violation(message):
    limit = int(automod_setting(message.guild.id, "spam_messages", 5))
    window = int(automod_setting(message.guild.id, "spam_seconds", 6))
    now = time.monotonic()
    key = (message.guild.id, message.author.id)
    bucket = [item for item in SPAM_BUCKETS.get(key, []) if now - item <= window]
    bucket.append(now)
    SPAM_BUCKETS[key] = bucket
    return len(bucket) >= limit, len(bucket), window


def find_violation(message):
    content = message.content or ""
    normalized = normalize_text(content)

    if automod_setting(message.guild.id, "anti_invite", True) and INVITE_RE.search(content):
        return "Discord daveti", "Mesajda Discord davet linki bulundu."

    if automod_setting(message.guild.id, "anti_links", False) and LINK_RE.search(content):
        return "Link", "Mesajda link bulundu."

    for word in automod_words(message.guild.id):
        if word and word in normalized:
            return "Yasak kelime", f"`{word}` yasak kelime listesinde."

    max_mentions = int(automod_setting(message.guild.id, "max_mentions", 6))
    mention_count = len(message.mentions) + len(message.role_mentions)
    if automod_setting(message.guild.id, "anti_mass_mention", True) and mention_count >= max_mentions:
        return "Cok etiket", f"Mesajda {mention_count} etiket var."

    is_spam, count, window = spam_violation(message)
    if automod_setting(message.guild.id, "anti_spam", True) and is_spam:
        return "Spam", f"{window} saniye icinde {count} mesaj."

    return None, None


async def delete_message(message):
    try:
        await message.delete()
        return True, None
    except discord.HTTPException as error:
        return False, str(error)


async def timeout_member(member, minutes, reason):
    try:
        await member.timeout(datetime.timedelta(minutes=minutes), reason=reason)
        return True, None
    except discord.HTTPException as error:
        return False, str(error)


async def apply_automod_action(message, label, detail):
    guild_id = message.guild.id
    action = str(automod_setting(guild_id, "action", "delete")).lower()
    if action not in VALID_ACTIONS:
        action = "delete"

    deleted, delete_error = await delete_message(message)
    warnings = None
    timed_out = False
    timeout_error = None
    reason = f"AutoMod: {label}"

    if action in {"warn", "timeout"}:
        warnings = add_warning(
            message.guild.id,
            message.author.id,
            {
                "moderator_id": message.guild.me.id if message.guild.me else 0,
                "moderator": "AutoMod",
                "reason": reason,
                "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }
        )

    if action == "timeout":
        minutes = int(automod_setting(guild_id, "timeout_minutes", 10))
        timed_out, timeout_error = await timeout_member(message.author, minutes, reason)

    fields = [
        ("Uye", f"{message.author} ({message.author.id})"),
        ("Kanal", f"{message.channel.mention} ({message.channel.id})"),
        ("Sebep", label),
        ("Detay", detail),
        ("Mesaj", trim(message.content or "Icerik yok", 900)),
        ("Aksiyon", action),
        ("Mesaj Silindi", "Evet" if deleted else f"Hayir: {delete_error}")
    ]
    if warnings is not None:
        fields.append(("Toplam Uyari", str(len(warnings))))
    if action == "timeout":
        fields.append(("Timeout", "Evet" if timed_out else f"Hayir: {timeout_error}"))

    await log_event(
        message.guild,
        with_emoji("shield", "AutoMod Engel"),
        f"{message.author.mention} mesaji AutoMod tarafindan engellendi.",
        0xE74C3C,
        fields,
        log_type="punishment"
    )

    try:
        warning = await message.channel.send(
            f"{message.author.mention} AutoMod: **{label}** sebebiyle mesaj engellendi.",
            delete_after=8
        )
        return warning is not None
    except discord.HTTPException:
        return True


async def handle_automod_message(message):
    if not message.guild or message.author.bot:
        return False
    if not isinstance(message.author, discord.Member):
        return False
    if not automod_enabled(message.guild.id) or can_bypass_automod(message.author):
        return False

    label, detail = find_violation(message)
    if not label:
        return False

    await apply_automod_action(message, label, detail)
    return True
