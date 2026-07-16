import discord
from discord import app_commands
from core.embeds import make_embed
from core.logging import log_event

# --- AYARLAR ---
# Butonlara basıp onay verecek yetkili rolün ID'si
VERIFIER_ROLE_ID = 1389930042200559706  

class VerifyDecisionView(discord.ui.View):
    def __init__(self, target_member: discord.Member, target_role: discord.Role):
        super().__init__(timeout=None)
        self.target_member = target_member
        self.target_role = target_role

    async def check_permissions(self, interaction: discord.Interaction) -> bool:
        is_admin = interaction.user.guild_permissions.administrator
        has_verifier_role = any(role.id == VERIFIER_ROLE_ID for role in interaction.user.roles)
        if is_admin or has_verifier_role:
            return True
            
        await interaction.response.send_message(
            embed=make_embed("Yetki Reddedildi", "Bu butonu sadece yöneticiler veya doğrulama yetkilileri kullanabilir.", 0xE74C3C),
            ephemeral=True
        )
        return False

    @discord.ui.button(label="Doğrula", style=discord.ButtonStyle.green, custom_id="btn_approve")
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_permissions(interaction):
            return

        member = interaction.guild.get_member(self.target_member.id)
        if not member:
            await interaction.response.send_message(
                embed=make_embed("Hata", "Doğrulanacak üye sunucudan ayrılmış.", 0xE74C3C),
                ephemeral=True
            )
            return

        if self.target_role in member.roles:
            await interaction.response.send_message(
                embed=make_embed("Hata", "Bu kullanıcı zaten bu role sahip.", 0xE74C3C),
                ephemeral=True
            )
            return

        try:
            await member.add_roles(self.target_role)
            for child in self.children:
                child.disabled = True
            
            embed = make_embed(
                "Doğrulama Onaylandı", 
                f"{member.mention} kullanıcısının doğrulama talebi {interaction.user.mention} tarafından **onaylandı** ve {self.target_role.mention} rolü verildi.", 
                0x2ECC71
            )
            await interaction.response.edit_message(embed=embed, view=self)

            await log_event(
                interaction.guild,
                "Manuel Doğrulama Onaylandı",
                f"{interaction.user} doğrulama talebini onayladı.",
                0x2ECC71,
                [
                    ("Onaylayan Yetkili", f"{interaction.user} ({interaction.user.id})"),
                    ("Doğrulanan Üye", f"{member} ({member.id})"),
                    ("Verilen Rol", f"{self.target_role.name}")
                ]
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                embed=make_embed("Hata", "Botun yetkisi bu rolü vermeye yetmiyor.", 0xE74C3C),
                ephemeral=True
            )

    @discord.ui.button(label="Reddet", style=discord.ButtonStyle.red, custom_id="btn_reject")
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_permissions(interaction):
            return

        for child in self.children:
            child.disabled = True

        embed = make_embed(
            "Doğrulama Reddedildi", 
            f"{self.target_member.mention} kullanıcısının doğrulama talebi {interaction.user.mention} tarafından **reddedildi**.", 
            0xE74C3C
        )
        await interaction.response.edit_message(embed=embed, view=self)

        await log_event(
            interaction.guild,
            "Manuel Doğrulama Reddedildi",
            f"{interaction.user} doğrulama talebini reddetti.",
            0xE74C3C,
            [
                ("Reddeden Yetkili", f"{interaction.user} ({interaction.user.id})"),
                ("Hedef Üye", f"{self.target_member} ({self.target_member.id})"),
                ("İstenen Rol", f"{self.target_role.name}")
            ]
        )

def register(bot):
    @bot.tree.command(name="verify", description="Belirttiğiniz kullanıcı için onay butonlu doğrulama talebi oluşturur.")
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.bot_has_permissions(manage_roles=True, send_messages=True, embed_links=True)
    async def verify(interaction: discord.Interaction, uye: discord.Member, rol: discord.Role):
        if rol in uye.roles:
            await interaction.response.send_message(
                embed=make_embed("Hata", "Bu kullanıcı zaten bu role sahip.", 0xE74C3C),
                ephemeral=True
            )
            return

        embed = make_embed(
            "Doğrulama Talebi",
            f"{uye.mention} ({uye.id}) kullanıcısına {rol.mention} rolünün verilmesi için bir talep oluşturuldu.\n\n"
            f"Lütfen aşağıdaki butonları kullanarak bu talebi onaylayın veya reddedin.",
            0xF1C40F
        )
        embed.set_footer(text="Bu işlemi yalnızca Yöneticiler ve yetkilendirilmiş roller gerçekleştirebilir.")

        view = VerifyDecisionView(target_member=uye, target_role=rol)
        await interaction.response.send_message(embed=embed, view=view)
