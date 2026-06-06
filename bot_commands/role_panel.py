import discord
from discord import app_commands

from core.auto_role import ROLE_PANEL_COLOR, ButtonRoleView
from core.embeds import make_embed
from core.logging import log_event
from core.permissions import role_hierarchy_error, self_assign_role_permission_error
from core.storage import set_guild_setting


def register(bot):
    @bot.tree.command(name="role-panel", description="Butona tiklayanlara rol veren paneli gonderir.")
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.bot_has_permissions(manage_roles=True, send_messages=True, embed_links=True)
    @app_commands.describe(
        role="Butona tiklayan uyelere verilecek rol.",
        channel="Panelin gonderilecegi kanal. Bos birakilirsa mevcut kanala gonderilir.",
        title="Panel basligi.",
        description="Panel aciklamasi."
    )
    async def role_panel(
        interaction,
        role: discord.Role,
        channel: discord.TextChannel | None = None,
        title: app_commands.Range[str, 1, 120] | None = None,
        description: app_commands.Range[str, 1, 800] | None = None
    ):
        error = role_hierarchy_error(interaction.guild, interaction.user, interaction.guild.me, role)
        error = error or self_assign_role_permission_error(role)
        if error:
            await interaction.response.send_message(
                embed=make_embed("Rol Paneli Kurulamadi", error, 0xE74C3C),
                ephemeral=True
            )
            return

        target_channel = channel or interaction.channel
        set_guild_setting(interaction.guild.id, "button_role_id", role.id)

        panel_title = title or "NEXOS Rol Paneli"
        panel_description = description or f"{role.mention} rolunu almak icin asagidaki butona bas."
        embed = make_embed(panel_title, panel_description, ROLE_PANEL_COLOR)
        embed.add_field(name="Verilecek Rol", value=role.mention, inline=True)
        embed.add_field(name="Sistem", value="Butona tiklayan uyeye rol otomatik verilir.", inline=False)
        embed.set_footer(text="Rol paneli guvenli rol sirasi ve yetki kontrolu ile calisir.")

        await target_channel.send(embed=embed, view=ButtonRoleView())
        await interaction.response.send_message(
            embed=make_embed("Rol Paneli Gonderildi", f"Panel {target_channel.mention} kanalina gonderildi.", 0x2ECC71),
            ephemeral=True
        )
        await log_event(
            interaction.guild,
            "Rol Paneli Gonderildi",
            f"Butonlu rol paneli {target_channel.mention} kanalina gonderildi.",
            0x2ECC71,
            [
                ("Yetkili", f"{interaction.user} ({interaction.user.id})"),
                ("Rol", f"{role} ({role.id})")
            ]
        )
