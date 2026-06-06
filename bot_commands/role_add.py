import discord
from discord import app_commands

from core.embeds import make_embed
from core.logging import log_event
from core.permissions import member_hierarchy_error, role_hierarchy_error


def register(bot):
    @bot.tree.command(name="role-add", description="Uyeye rol verir.")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_roles=True)
    @app_commands.checks.bot_has_permissions(manage_roles=True, embed_links=True)
    async def role_add(interaction, member: discord.Member, role: discord.Role):
        error = member_hierarchy_error(interaction.guild, interaction.user, interaction.guild.me, member)
        error = error or role_hierarchy_error(interaction.guild, interaction.user, interaction.guild.me, role)
        if error:
            await interaction.response.send_message(
                embed=make_embed("Rol Verilemedi", error, 0xE74C3C),
                ephemeral=True
            )
            return

        await member.add_roles(role, reason=f"{interaction.user} tarafindan rol verildi")
        await interaction.response.send_message(
            embed=make_embed("Rol verildi", f"{member.mention} uyesine {role.mention} rolu verildi.", 0x2ECC71)
        )
        await log_event(
            interaction.guild,
            "Moderasyon: Rol Verildi",
            f"{member} uyesine {role} rolu verildi.",
            0x2ECC71,
            [
                ("Yetkili", f"{interaction.user} ({interaction.user.id})"),
                ("Uye", f"{member} ({member.id})"),
                ("Rol", f"{role} ({role.id})")
            ]
        )
