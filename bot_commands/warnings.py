import discord
from discord import app_commands

from core.embeds import make_embed
from core.storage import get_warnings


def warning_line(index, item):
    reason = item.get("reason", "Sebep yok")
    moderator_id = item.get("moderator_id")
    moderator = f"<@{moderator_id}>" if moderator_id else item.get("moderator", "Bilinmiyor")
    return f"{index + 1}. {reason} - {moderator}"


def register(bot):
    @bot.tree.command(name="warnings", description="Uyenin uyarilarini listeler.")
    @app_commands.guild_only()
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def warnings_command(interaction, member: discord.Member):
        warnings = get_warnings(interaction.guild.id, member.id)
        if not warnings:
            description = "Uyari yok."
        else:
            description = "\n".join(
                warning_line(index, item)
                for index, item in enumerate(warnings)
            )
        await interaction.response.send_message(
            embed=make_embed(f"{member} uyarilari", description, 0xF1C40F),
            ephemeral=True
        )
