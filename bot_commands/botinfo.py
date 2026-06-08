import discord
from discord import app_commands

from core.embeds import make_embed
from core.emojis import emoji, with_emoji


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

        embed = make_embed(
            with_emoji("galaxy", "NEXOS"),
            "Moderasyon, ekonomi, ticket, cekilis, welcome karti, buton rol ve full log sistemi aktif.",
            0x8B5CF6
        )
        embed.add_field(name=f"{emoji('rocket')} Gecikme", value=f"{round(bot.latency * 1000)}ms", inline=True)
        embed.add_field(name=f"{emoji('server')} Sunucu Sayisi", value=str(guild_count), inline=True)
        embed.add_field(name=f"{emoji('member')} Kullanici", value=str(user_count), inline=True)
        embed.add_field(name=f"{emoji('settings')} Slash Komut", value=str(command_count), inline=True)
        embed.add_field(name=f"{emoji('shield')} Log Paketi", value="Mesaj, uye, rol, kanal, ses, ban, emoji", inline=False)
        embed.add_field(name=f"{emoji('bot')} discord.py", value=discord.__version__, inline=True)
        if bot.user:
            embed.set_thumbnail(url=bot.user.display_avatar.url)
        embed.set_footer(text="NEXOS Ultimate Galaxy")
        await interaction.response.send_message(embed=embed, ephemeral=True)
