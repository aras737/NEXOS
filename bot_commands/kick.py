import discord
from discord import app_commands

from core.embeds import make_embed
from core.moderation import can_moderate, send_error


def register(bot):
    @bot.tree.command(name="kick", description="Uyeyi sunucudan atar.")
    @app_commands.guild_only()
    @app_commands.default_permissions(kick_members=True)
    @app_commands.checks.bot_has_permissions(kick_members=True, embed_links=True)
    async def kick(interaction, member: discord.Member, reason: str = "Sebep belirtilmedi"):
        issue = can_moderate(interaction, member)
        if issue:
            return await send_error(interaction, issue)

        await member.kick(reason=reason)
        await interaction.response.send_message(
            embed=make_embed("Uye atildi", f"{member.mention} sunucudan atildi.\nSebep: {reason}", 0x2ECC71)
        )
