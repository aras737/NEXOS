from discord import app_commands

from core.embeds import make_embed


def register(bot):
    @bot.tree.command(name="unlock", description="Bulundugun kanalin kilidini acar.")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_channels=True)
    @app_commands.checks.bot_has_permissions(manage_channels=True)
    async def unlock(interaction):
        await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=None)
        await interaction.response.send_message(
            embed=make_embed("Kanal acildi", "Bu kanalda mesaj gonderme izni normale dondu.", 0x2ECC71)
        )
