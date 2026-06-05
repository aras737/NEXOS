import discord
from discord import app_commands

from core.embeds import make_embed


def register(bot):
    @bot.tree.command(name="untimeout", description="Uyenin susturmasini kaldirir.")
    @app_commands.guild_only()
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.checks.bot_has_permissions(moderate_members=True, embed_links=True)
    async def untimeout(interaction, member: discord.Member, reason: str = "Sebep belirtilmedi"):
        await member.timeout(None, reason=reason)
        await interaction.response.send_message(
            embed=make_embed("Susturma kaldirildi", f"{member.mention} susturmasi kaldirildi.", 0x2ECC71)
        )
