import discord
from discord import app_commands

from core.embeds import make_embed


def register(bot):
    @bot.tree.command(name="botinfo", description="Bot sistem bilgisini gosterir.")
    @app_commands.guild_only()
    @app_commands.default_permissions(send_messages=True)
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def botinfo(interaction):
        bot = interaction.client
        guild_count = len(bot.guilds)
        user_count = sum(guild.member_count or 0 for guild in bot.guilds)
        command_count = len(bot.tree.get_commands())

        embed = make_embed("NEXOS", "Moderasyon, ekonomi ve log sistemi aktif.", 0x5865F2)
        embed.add_field(name="Gecikme", value=f"{round(bot.latency * 1000)}ms", inline=True)
        embed.add_field(name="Sunucu", value=str(guild_count), inline=True)
        embed.add_field(name="Kullanici", value=str(user_count), inline=True)
        embed.add_field(name="Slash Komut", value=str(command_count), inline=True)
        embed.add_field(name="discord.py", value=discord.__version__, inline=True)
        embed.set_footer(text="NEXOS Ultimate")
        await interaction.response.send_message(embed=embed, ephemeral=True)
