from discord import app_commands

from core.embeds import make_embed
from core.logging import log_event


def register(bot):
    @bot.tree.command(name="slowmode", description="Kanal yavas modunu ayarlar.")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_channels=True)
    @app_commands.checks.bot_has_permissions(manage_channels=True, embed_links=True)
    async def slowmode(interaction, seconds: app_commands.Range[int, 0, 21600]):
        await interaction.channel.edit(slowmode_delay=seconds)
        await interaction.response.send_message(
            embed=make_embed("Yavas mod ayarlandi", f"Yavas mod: {seconds} saniye.", 0x2ECC71)
        )
        await log_event(
            interaction.guild,
            "Moderasyon: Slowmode",
            f"{interaction.channel} yavas modu {seconds} saniye yapildi.",
            0x3498DB,
            [("Yetkili", f"{interaction.user} ({interaction.user.id})")]
        )
