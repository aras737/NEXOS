from discord import app_commands

from core.embeds import make_embed


def register(bot):
    @bot.tree.command(name="embed", description="Embed mesaj gonderir.")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_messages=True)
    async def embed(interaction, title: str, description: str):
        await interaction.channel.send(embed=make_embed(title, description))
        await interaction.response.send_message("Gonderildi.", ephemeral=True)
