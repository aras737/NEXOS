import discord

from core.embeds import make_embed
from core.storage import get_guild_setting


WELCOME_COLOR = 0x8B5CF6
LEAVE_COLOR = 0x34495E

DEFAULT_WELCOME_MESSAGE = (
    "{mention}, NEXOS galaksisine hos geldin. Yildiz rotan {server} sunucusunda basladi; "
    "artik {count}. uyemizsin."
)
DEFAULT_LEAVE_MESSAGE = "{user} galaksiden ayrildi. {server} artik {count} uyeye sahip."


def render_member_text(template, member):
    guild = member.guild
    count = guild.member_count or len(guild.members)
    values = {
        "{mention}": member.mention,
        "{user}": str(member),
        "{name}": member.display_name,
        "{server}": guild.name,
        "{count}": str(count)
    }
    text = str(template or "")
    for key, value in values.items():
        text = text.replace(key, value)
    return text


def configured_text_channel(guild, key):
    channel_id = get_guild_setting(guild.id, key)
    if not channel_id:
        return None
    channel = guild.get_channel(int(channel_id))
    return channel if isinstance(channel, discord.TextChannel) else None


async def send_member_welcome(member):
    if get_guild_setting(member.guild.id, "welcome_enabled", True) is False:
        return False

    channel = configured_text_channel(member.guild, "welcome_channel_id") or member.guild.system_channel
    if not channel:
        return False

    message = get_guild_setting(member.guild.id, "welcome_message", DEFAULT_WELCOME_MESSAGE)
    embed = make_embed(
        "NEXOS Galaksiye Hos Geldin",
        render_member_text(message, member),
        WELCOME_COLOR
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="Sunucu", value=member.guild.name, inline=True)
    embed.add_field(name="Uye Sayisi", value=str(member.guild.member_count or len(member.guild.members)), inline=True)
    embed.set_footer(text="Galaksi kaydi basariyla tamamlandi.")

    try:
        await channel.send(content=member.mention, embed=embed)
        return True
    except discord.HTTPException:
        return False


async def send_member_leave(member):
    if get_guild_setting(member.guild.id, "welcome_enabled", True) is False:
        return False

    channel = (
        configured_text_channel(member.guild, "leave_channel_id")
        or configured_text_channel(member.guild, "welcome_channel_id")
    )
    if not channel:
        return False

    message = get_guild_setting(member.guild.id, "leave_message", DEFAULT_LEAVE_MESSAGE)
    embed = make_embed(
        "NEXOS Galaksi Cikisi",
        render_member_text(message, member),
        LEAVE_COLOR
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="Sunucu", value=member.guild.name, inline=True)
    embed.add_field(name="Kalan Uye", value=str(member.guild.member_count or len(member.guild.members)), inline=True)

    try:
        await channel.send(embed=embed)
        return True
    except discord.HTTPException:
        return False
