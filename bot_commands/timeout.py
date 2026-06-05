import datetime

import discord
from discord import app_commands

from core.embeds import make_embed
from core.logging import log_event
from core.moderation import can_moderate, send_error


def register(bot):
    @bot.tree.command(name="timeout", description="Uyeyi gecici susturur.")
    @app_commands.guild_only()
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.checks.bot_has_permissions(moderate_members=True, embed_links=True)
    async def timeout(
        interaction,
        member: discord.Member,
        minutes: app_commands.Range[int, 1, 40320],
        reason: str = "Sebep belirtilmedi"
    ):
        issue = can_moderate(interaction, member)
        if issue:
            return await send_error(interaction, issue)

        await member.timeout(datetime.timedelta(minutes=minutes), reason=reason)
        await interaction.response.send_message(
            embed=make_embed("Uye susturuldu", f"{member.mention} {minutes} dakika susturuldu.", 0x2ECC71)
        )
        await log_event(
            interaction.guild,
            "Moderasyon: Timeout",
            f"{member} {minutes} dakika susturuldu.",
            0xE67E22,
            [
                ("Yetkili", f"{interaction.user} ({interaction.user.id})"),
                ("Uye", f"{member} ({member.id})"),
                ("Sebep", reason)
            ]
        )
