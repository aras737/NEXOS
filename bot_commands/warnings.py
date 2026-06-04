import discord
from discord import app_commands

from core.embeds import make_embed
from core.storage import get_warnings


def register(bot):
    @bot.tree.command(name="warnings", description="Uyenin uyarilarini listeler.")
    @app_commands.guild_only()
    @app_commands.default_permissions(moderate_members=True)
    async def warnings_command(interaction, member: discord.Member):
        warnings = get_warnings(interaction.guild.id, member.id)
        if not warnings:
            description = "Uyari yok."
        else:
            description = "\n".join(
                f"{index + 1}. {item['reason']} - <@{item['moderator_id']}>"
                for index, item in enumerate(warnings)
            )
        await interaction.response.send_message(
            embed=make_embed(f"{member} uyarilari", description, 0xF1C40F),
            ephemeral=True
        )
