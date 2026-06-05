from discord import app_commands

from core.embeds import make_embed


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
