import discord

from core.config import MEMBER_COUNT_CHANNEL_ID


def member_count_name(guild):
    return f"uyeler-{guild.member_count}"


async def update_member_count_channel(guild):
    if not MEMBER_COUNT_CHANNEL_ID:
        return

    channel = guild.get_channel(MEMBER_COUNT_CHANNEL_ID)
    if not channel:
        return

    new_name = member_count_name(guild)
    if getattr(channel, "name", None) == new_name:
        return

    if isinstance(channel, (discord.TextChannel, discord.VoiceChannel, discord.StageChannel, discord.CategoryChannel)):
        await channel.edit(name=new_name, reason="NEXOS uye sayaci guncellendi")
