from discord import app_commands

from core.embeds import make_embed


def register(bot):
    @bot.tree.command(name="slowmode", description="Kanal yavas modunu ayarlar.")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_channels=True)
    @app_commands.checks.bot_has_permissions(manage_channels=True)
    async def slowmode(interaction, seconds: app_commands.Range[int, 0, 21600]):
        await interaction.channel.edit(slowmode_delay=seconds)
        await interaction.response.send_message(
            embed=make_embed("Yavas mod ayarlandi", f"Yavas mod: {seconds} saniye.", 0x2ECC71)
        )
