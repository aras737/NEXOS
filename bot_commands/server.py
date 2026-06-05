import discord
from discord import app_commands

from core.embeds import make_embed


def register(bot):
    @bot.tree.command(name="server", description="Sunucu bilgilerini gosterir.")
    @app_commands.guild_only()
    @app_commands.default_permissions(send_messages=True)
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def server(interaction):
        guild = interaction.guild
        embed = make_embed(guild.name, "Sunucu bilgileri", 0x3498DB)
        embed.add_field(name="Uyeler", value=str(guild.member_count), inline=True)
        embed.add_field(name="Kanallar", value=str(len(guild.channels)), inline=True)
        embed.add_field(name="Roller", value=str(len(guild.roles)), inline=True)
        embed.add_field(name="Olusturma", value=discord.utils.format_dt(guild.created_at, "D"), inline=True)
        await interaction.response.send_message(embed=embed)
