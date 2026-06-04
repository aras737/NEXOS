import discord
from discord import app_commands

from core.embeds import make_embed


def register(bot):
    @bot.tree.command(name="user", description="Uye bilgilerini gosterir.")
    @app_commands.guild_only()
    async def user(interaction, member: discord.Member | None = None):
        member = member or interaction.user
        embed = make_embed(str(member), "Uye bilgileri", 0x3498DB)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="ID", value=str(member.id), inline=True)
        embed.add_field(name="Hesap", value=discord.utils.format_dt(member.created_at, "D"), inline=True)
        embed.add_field(name="Katilim", value=discord.utils.format_dt(member.joined_at, "D"), inline=True)
        await interaction.response.send_message(embed=embed)
