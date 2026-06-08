import discord

from core.config import VOICE_CHANNEL_ID
from core.embeds import make_embed
from core.emojis import with_emoji
from core.logging import log_event, trim
from core.music import ffmpeg_executable, require_ffmpeg
from core.storage import get_guild_setting


def setting_list(guild_id, key):
    value = get_guild_setting(guild_id, key, [])
    if not isinstance(value, list):
        return []
    return [int(item) for item in value if str(item).isdigit()]


def configured_voice_channel(guild):
    channel_id = get_guild_setting(guild.id, "voice_welcome_channel_id") or VOICE_CHANNEL_ID
    if not channel_id:
        return None
    channel = guild.get_channel(int(channel_id))
    return channel if isinstance(channel, discord.VoiceChannel) else None


def has_any_role(member, role_ids):
    if not role_ids:
        return False
    member_role_ids = {role.id for role in member.roles}
    return bool(member_role_ids.intersection(role_ids))


def count_members_with_roles(channel, role_ids):
    if not role_ids:
        return len([member for member in channel.members if not member.bot])
    return len([member for member in channel.members if not member.bot and has_any_role(member, role_ids)])


def role_mentions(guild, role_ids):
    mentions = []
    for role_id in role_ids:
        role = guild.get_role(int(role_id))
        if role:
            mentions.append(role.mention)
    return ", ".join(mentions) if mentions else "Ayarlanmadi"


def voice_channel_label(channel):
    return f"{channel.mention} ({channel.id})" if channel else "Ayarlanmadi"


def sound_source(guild, key):
    return get_guild_setting(guild.id, key)


async def ensure_voice_welcome_client(channel):
    voice_client = channel.guild.voice_client
    if voice_client and voice_client.is_connected():
        if voice_client.channel != channel:
            await voice_client.move_to(channel)
        return voice_client
    return await channel.connect()


async def play_voice_welcome_sound(guild, channel, source, title, member):
    voice_client = guild.voice_client
    if voice_client and (voice_client.is_playing() or voice_client.is_paused()):
        await log_event(
            guild,
            with_emoji("voice", "Voice Welcome Atlandi"),
            "Bot su an baska bir ses oynatiyor.",
            0xF59E0B,
            [("Uye", f"{member} ({member.id})"), ("Kanal", voice_channel_label(channel))],
            log_type="voice"
        )
        return False

    try:
        require_ffmpeg()
        voice_client = await ensure_voice_welcome_client(channel)
    except Exception as error:
        await log_event(
            guild,
            with_emoji("voice", "Voice Welcome Baglanti Hata"),
            "Bot voice welcome kanalina baglanamadi.",
            0xE74C3C,
            [
                ("Uye", f"{member} ({member.id})"),
                ("Kanal", voice_channel_label(channel)),
                ("Hata", trim(error, 700))
            ],
            log_type="voice"
        )
        return False

    try:
        audio = discord.FFmpegPCMAudio(source, executable=ffmpeg_executable())
        voice_client.play(audio)
    except Exception as error:
        await log_event(
            guild,
            with_emoji("voice", "Voice Welcome Hata"),
            "Voice welcome sesi baslatilamadi.",
            0xE74C3C,
            [
                ("Uye", f"{member} ({member.id})"),
                ("Kanal", voice_channel_label(channel)),
                ("Kaynak", trim(source, 700)),
                ("Hata", trim(error, 700))
            ],
            log_type="voice"
        )
        return False

    await log_event(
        guild,
        with_emoji("voice", title),
        f"{member.mention} icin voice welcome sesi calindi.",
        0x22C55E,
        [
            ("Uye", f"{member} ({member.id})"),
            ("Kanal", voice_channel_label(channel)),
            ("Kaynak", trim(source, 700))
        ],
        log_type="voice"
    )
    return True


async def handle_voice_welcome(member, before, after):
    if member.bot or not member.guild:
        return False
    if get_guild_setting(member.guild.id, "voice_welcome_enabled", False) is False:
        return False
    if before.channel == after.channel or not after.channel:
        return False

    channel = configured_voice_channel(member.guild)
    if not channel or after.channel.id != channel.id:
        return False

    staff_role_ids = setting_list(member.guild.id, "voice_welcome_staff_role_ids")
    unregistered_role_ids = setting_list(member.guild.id, "voice_welcome_unregistered_role_ids")
    if unregistered_role_ids and not has_any_role(member, unregistered_role_ids):
        return False

    staff_count = count_members_with_roles(channel, staff_role_ids) if staff_role_ids else 0
    unregistered_count = count_members_with_roles(channel, unregistered_role_ids)
    welcome_sound = sound_source(member.guild, "voice_welcome_sound")
    staff_sound = sound_source(member.guild, "voice_welcome_staff_sound")

    source = None
    title = "Voice Welcome"
    if staff_role_ids and staff_count == 1 and unregistered_count == 1 and staff_sound:
        source = staff_sound
        title = "Yetkili Voice Welcome"
    elif unregistered_count == 1 and welcome_sound:
        source = welcome_sound

    if not source:
        await log_event(
            member.guild,
            with_emoji("voice", "Voice Welcome Sesi Yok"),
            "Voice welcome tetiklendi ama calinacak ses kaynagi ayarlanmamis.",
            0xF59E0B,
            [
                ("Uye", f"{member} ({member.id})"),
                ("Kanal", voice_channel_label(channel)),
                ("Yetkili Rolleri", role_mentions(member.guild, staff_role_ids)),
                ("Kayitsiz Rolleri", role_mentions(member.guild, unregistered_role_ids))
            ],
            log_type="voice"
        )
        return False

    return await play_voice_welcome_sound(member.guild, channel, source, title, member)


def voice_welcome_settings_embed(guild):
    channel = configured_voice_channel(guild)
    staff_role_ids = setting_list(guild.id, "voice_welcome_staff_role_ids")
    unregistered_role_ids = setting_list(guild.id, "voice_welcome_unregistered_role_ids")
    enabled = get_guild_setting(guild.id, "voice_welcome_enabled", False)
    welcome_sound = sound_source(guild, "voice_welcome_sound")
    staff_sound = sound_source(guild, "voice_welcome_staff_sound")

    embed = make_embed(
        with_emoji("voice", "Voice Welcome Ayarlari"),
        "Belirlenen ses kanalina girislerde kisa ses calar.",
        0x8B5CF6
    )
    embed.add_field(name="Durum", value="Acik" if enabled else "Kapali", inline=True)
    embed.add_field(name="Kanal", value=voice_channel_label(channel), inline=False)
    embed.add_field(name="Welcome Ses", value=trim(welcome_sound or "Ayarlanmadi", 1024), inline=False)
    embed.add_field(name="Yetkili Ses", value=trim(staff_sound or "Ayarlanmadi", 1024), inline=False)
    embed.add_field(name="Yetkili Rolleri", value=role_mentions(guild, staff_role_ids), inline=False)
    embed.add_field(name="Kayitsiz Rolleri", value=role_mentions(guild, unregistered_role_ids), inline=False)
    return embed
