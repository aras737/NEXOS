from discord import app_commands

from core.embeds import make_embed
from core.logging import log_event


def register(bot):
    @bot.tree.command(name="lock", description="Bulundugun kanali kilitler.")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_channels=True)
    @app_commands.checks.bot_has_permissions(manage_channels=True, embed_links=True)
    async def lock(interaction):
        await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
        await interaction.response.send_message(
            embed=make_embed("Kanal kilitlendi", "Bu kanalda mesaj gonderme kapatildi.", 0x2ECC71)
        )
        await log_event(
            interaction.guild,
            "Moderasyon: Kanal Kilitlendi",
            f"{interaction.channel} kilitlendi.",
            0xE67E22,
            [("Yetkili", f"{interaction.user} ({interaction.user.id})")]
        )
