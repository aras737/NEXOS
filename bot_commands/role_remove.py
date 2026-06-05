import discord
from discord import app_commands

from core.embeds import make_embed
from core.logging import log_event


def register(bot):
    @bot.tree.command(name="role-remove", description="Uyeden rol alir.")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_roles=True)
    @app_commands.checks.bot_has_permissions(manage_roles=True, embed_links=True)
    async def role_remove(interaction, member: discord.Member, role: discord.Role):
        await member.remove_roles(role, reason=f"{interaction.user} tarafindan rol alindi")
        await interaction.response.send_message(
            embed=make_embed("Rol alindi", f"{member.mention} uyesinden {role.mention} rolu alindi.", 0x2ECC71)
        )
        await log_event(
            interaction.guild,
            "Moderasyon: Rol Alindi",
            f"{member} uyesinden {role} rolu alindi.",
            0xE67E22,
            [
                ("Yetkili", f"{interaction.user} ({interaction.user.id})"),
                ("Uye", f"{member} ({member.id})"),
                ("Rol", f"{role} ({role.id})")
            ]
        )
