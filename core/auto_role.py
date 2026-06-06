import discord

from core.embeds import make_embed
from core.logging import log_event
from core.permissions import role_hierarchy_error, self_assign_role_permission_error
from core.storage import get_guild_setting


ROLE_PANEL_COLOR = 0x7C3AED


async def apply_auto_role(member):
    role_id = get_guild_setting(member.guild.id, "auto_role_id")
    if not role_id:
        return

    role = member.guild.get_role(int(role_id))
    if not role:
        await log_event(
            member.guild,
            "Oto Rol Hata",
            f"Oto rol bulunamadi: {role_id}",
            0xE74C3C
        )
        return

    error = role_hierarchy_error(member.guild, member, member.guild.me, role, check_actor=False)
    error = error or self_assign_role_permission_error(role, "Oto rol")
    if error:
        await log_event(
            member.guild,
            "Oto Rol Hata",
            f"{member} uyesine oto rol verilemedi.",
            0xE74C3C,
            [
                ("Rol", f"{role} ({role.id})"),
                ("Hata", error)
            ]
        )
        return

    try:
        await member.add_roles(role, reason="NEXOS oto rol")
        await log_event(
            member.guild,
            "Oto Rol Verildi",
            f"{member.mention} uyesine {role.mention} verildi.",
            0x2ECC71,
            [("Uye", f"{member} ({member.id})")]
        )
    except Exception as error:
        await log_event(
            member.guild,
            "Oto Rol Hata",
            f"{member} uyesine oto rol verilemedi.",
            0xE74C3C,
            [
                ("Rol", f"{role} ({role.id})"),
                ("Hata", f"{type(error).__name__}: {error}")
            ]
        )


class ButtonRoleView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Rolu Al", style=discord.ButtonStyle.primary, custom_id="nexos:button_role")
    async def role_button(self, interaction, _button):
        if not interaction.guild:
            await interaction.response.send_message("Bu buton sadece sunucuda kullanilir.", ephemeral=True)
            return

        role_id = get_guild_setting(interaction.guild.id, "button_role_id")
        if not role_id:
            await interaction.response.send_message(
                embed=make_embed("Rol Ayarlanmamis", "Bu panel icin rol ayari bulunamadi.", 0xE74C3C),
                ephemeral=True
            )
            return

        role = interaction.guild.get_role(int(role_id))
        if not role:
            await interaction.response.send_message(
                embed=make_embed("Rol Bulunamadi", "Ayarlanan rol artik sunucuda yok.", 0xE74C3C),
                ephemeral=True
            )
            return

        if role in interaction.user.roles:
            await interaction.response.send_message(
                embed=make_embed("Rol Zaten Var", f"{role.mention} rolu zaten sende var.", 0xE67E22),
                ephemeral=True
            )
            return

        error = role_hierarchy_error(interaction.guild, interaction.user, interaction.guild.me, role, check_actor=False)
        error = error or self_assign_role_permission_error(role)
        if error:
            await interaction.response.send_message(
                embed=make_embed("Rol Verilemedi", error, 0xE74C3C),
                ephemeral=True
            )
            await log_event(
                interaction.guild,
                "Buton Rol Hata",
                f"{interaction.user} buton rolunu alamadi.",
                0xE74C3C,
                [("Rol", f"{role} ({role.id})"), ("Hata", error)]
            )
            return

        try:
            await interaction.user.add_roles(role, reason="NEXOS buton rol paneli")
        except discord.HTTPException as error:
            await interaction.response.send_message(
                embed=make_embed("Rol Verilemedi", f"Discord rol vermeyi reddetti: {type(error).__name__}", 0xE74C3C),
                ephemeral=True
            )
            await log_event(
                interaction.guild,
                "Buton Rol Hata",
                f"{interaction.user} buton rolunu alamadi.",
                0xE74C3C,
                [("Rol", f"{role} ({role.id})"), ("Hata", f"{type(error).__name__}: {error}")]
            )
            return

        await interaction.response.send_message(
            embed=make_embed("Rol Verildi", f"{role.mention} rolu hesabina eklendi.", 0x2ECC71),
            ephemeral=True
        )
        await log_event(
            interaction.guild,
            "Buton Rol Verildi",
            f"{interaction.user} butondan rol aldi.",
            0x2ECC71,
            [
                ("Uye", f"{interaction.user} ({interaction.user.id})"),
                ("Rol", f"{role} ({role.id})")
            ]
        )
