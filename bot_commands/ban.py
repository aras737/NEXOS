import discord
from discord import app_commands

from core.embeds import make_embed
from core.logging import log_event
from core.moderation import can_moderate, send_error


def register(bot):
    @bot.tree.command(name="ban", description="Uyeyi banlar.")
    @app_commands.guild_only()
    @app_commands.default_permissions(ban_members=True)
    @app_commands.checks.bot_has_permissions(ban_members=True, embed_links=True)
    async def ban(interaction, member: discord.Member, reason: str = "Sebep belirtilmedi"):
        issue = can_moderate(interaction, member)
        if issue:
            return await send_error(interaction, issue)

        await member.ban(reason=reason, delete_message_days=0)
        await interaction.response.send_message(
            embed=make_embed("Uye banlandi", f"{member} banlandi.\nSebep: {reason}", 0x2ECC71)
        )
        await log_event(
            interaction.guild,
            "Moderasyon: Ban",
            f"{member} banlandi.",
            0xE74C3C,
            [
                ("Yetkili", f"{interaction.user} ({interaction.user.id})"),
                ("Uye", f"{member} ({member.id})"),
                ("Sebep", reason)
            ]
        )
