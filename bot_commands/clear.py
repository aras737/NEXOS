from discord import app_commands

from core.embeds import make_embed


def register(bot):
    @bot.tree.command(name="clear", description="Kanaldan mesaj siler.")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.checks.bot_has_permissions(manage_messages=True, embed_links=True)
    async def clear(interaction, amount: app_commands.Range[int, 1, 100]):
        deleted = await interaction.channel.purge(limit=amount)
        await interaction.response.send_message(
            embed=make_embed("Mesajlar silindi", f"{len(deleted)} mesaj silindi.", 0x2ECC71),
            ephemeral=True
        )
