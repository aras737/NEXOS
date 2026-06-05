import discord
from discord import app_commands

from core.economy import reset_account
from core.embeds import make_embed
from core.logging import log_event


def register(bot):
    @bot.tree.command(name="eco-reset", description="Yetkili olarak uye ekonomi hesabini sifirlar.")
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def eco_reset(interaction, member: discord.Member, reason: str = "Sebep belirtilmedi"):
        reset_account(interaction.guild.id, member.id)
        await interaction.response.send_message(
            embed=make_embed("Ekonomi Sifirlandi", f"{member.mention} ekonomi hesabi sifirlandi.", 0xE74C3C),
            ephemeral=True
        )
        await log_event(
            interaction.guild,
            "Eco Reset",
            f"{member} ekonomi hesabi sifirlandi.",
            0xE74C3C,
            [
                ("Yetkili", f"{interaction.user} ({interaction.user.id})"),
                ("Uye", f"{member} ({member.id})"),
                ("Sebep", reason)
            ]
        )
