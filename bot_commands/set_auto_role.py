import discord
from discord import app_commands

from core.embeds import make_embed
from core.logging import log_event
from core.permissions import role_hierarchy_error, self_assign_role_permission_error
from core.storage import set_guild_setting


def register(bot):
    @bot.tree.command(name="set-auto-role", description="Yeni gelen uyelere otomatik verilecek rolu ayarlar.")
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.bot_has_permissions(manage_roles=True, embed_links=True)
    async def set_auto_role(interaction, role: discord.Role | None = None):
        if role is None:
            set_guild_setting(interaction.guild.id, "auto_role_id", None)
            await interaction.response.send_message(
                embed=make_embed("Oto Rol Kapatildi", "Yeni gelen uyelere otomatik rol verilmeyecek.", 0xE67E22),
                ephemeral=True
            )
            await log_event(
                interaction.guild,
                "Oto Rol Kapatildi",
                f"{interaction.user} oto rol sistemini kapatti.",
                0xE67E22
            )
            return

        error = role_hierarchy_error(interaction.guild, interaction.user, interaction.guild.me, role)
        error = error or self_assign_role_permission_error(role, "Oto rol")
        if error:
            await interaction.response.send_message(
                embed=make_embed("Rol Ayarlanamadi", error, 0xE74C3C),
                ephemeral=True
            )
            return

        set_guild_setting(interaction.guild.id, "auto_role_id", role.id)
        await interaction.response.send_message(
            embed=make_embed("Oto Rol Ayarlandi", f"Yeni gelen uyelere {role.mention} verilecek.", 0x2ECC71),
            ephemeral=True
        )
        await log_event(
            interaction.guild,
            "Oto Rol Ayarlandi",
            f"Yeni oto rol: {role.mention}",
            0x2ECC71,
            [("Yetkili", f"{interaction.user} ({interaction.user.id})")]
        )
