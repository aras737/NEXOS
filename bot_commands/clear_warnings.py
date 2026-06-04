import discord
from discord import app_commands

from core.embeds import make_embed
from core.storage import clear_user_warnings


def register(bot):
    @bot.tree.command(name="clear-warnings", description="Uyenin uyarilarini temizler.")
    @app_commands.guild_only()
    @app_commands.default_permissions(moderate_members=True)
    async def clear_warnings_command(interaction, member: discord.Member):
        clear_user_warnings(interaction.guild.id, member.id)
        await interaction.response.send_message(
            embed=make_embed("Uyarilar temizlendi", f"{member.mention} uyarilari temizlendi.", 0x2ECC71),
            ephemeral=True
        )
