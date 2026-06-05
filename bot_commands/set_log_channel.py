import discord
from discord import app_commands

from core.embeds import make_embed
from core.logging import log_event
from core.storage import set_guild_setting


def register(bot):
    @bot.tree.command(name="set-log-channel", description="Log kanalini ayarlar.")
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.bot_has_permissions(embed_links=True, send_messages=True)
    async def set_log_channel(interaction, channel: discord.TextChannel):
        set_guild_setting(interaction.guild.id, "log_channel_id", channel.id)
        await interaction.response.send_message(
            embed=make_embed("Log kanali ayarlandi", f"Loglar artik {channel.mention} kanalina gonderilecek.", 0x2ECC71),
            ephemeral=True
        )
        await log_event(
            interaction.guild,
            "Log Kanali Ayarlandi",
            f"Yeni log kanali: {channel.mention}",
            0x2ECC71,
            [("Yetkili", f"{interaction.user} ({interaction.user.id})")]
        )
