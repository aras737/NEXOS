from discord import app_commands

from core.embeds import make_embed


def register(bot):
    @bot.tree.command(name="embed", description="Embed mesaj gonderir.")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.checks.bot_has_permissions(send_messages=True, embed_links=True)
    async def embed(interaction, title: app_commands.Range[str, 1, 256], description: app_commands.Range[str, 1, 1900]):
        await interaction.response.defer(ephemeral=True)
        await interaction.channel.send(embed=make_embed(title, description))
        await interaction.followup.send("Gonderildi.", ephemeral=True)
