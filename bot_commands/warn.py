import datetime

import discord
from discord import app_commands

from core.embeds import make_embed
from core.logging import log_event
from core.storage import add_warning


def register(bot):
    @bot.tree.command(name="warn", description="Uyeye uyari verir.")
    @app_commands.guild_only()
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def warn(interaction, member: discord.Member, reason: str):
        warnings = add_warning(
            interaction.guild.id,
            member.id,
            {
                "reason": reason,
                "moderator_id": interaction.user.id,
                "created_at": datetime.datetime.utcnow().isoformat()
            }
        )
        await interaction.response.send_message(
            embed=make_embed("Uyari verildi", f"{member.mention} uyarildi. Toplam uyari: {len(warnings)}", 0xF1C40F)
        )
        await log_event(
            interaction.guild,
            "Moderasyon: Warn",
            f"{member} uyarildi.",
            0xF1C40F,
            [
                ("Yetkili", f"{interaction.user} ({interaction.user.id})"),
                ("Uye", f"{member} ({member.id})"),
                ("Sebep", reason),
                ("Toplam Uyari", len(warnings))
            ]
        )
