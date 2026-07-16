import discord
from discord import app_commands
from discord.ext import commands

# Butonun bot kapandığında bile çalışabilmesi için kalıcı (persistent) bir View tanımlıyoruz
class VerifyView(discord.ui.View):
    def __init__(self):
        # timeout=None kalıcı olmasını sağlar
        super().__init__(timeout=None)

    # discord.js'teki 'forces_verify_btn' custom id'sini buraya atıyoruz
    @discord.ui.button(
        label="Doğrula", 
        style=discord.ButtonStyle.success, 
        custom_id="forces_verify_btn", 
        emoji="✅"
    )
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Kullanıcı butona tıkladığında tetiklenecek fonksiyon"""
        
        # Örnek: Kullanıcıya rol vermek isterseniz:
        # role = interaction.guild.get_role(1527008029877207050)
        # await interaction.user.add_roles(role)
        
        await interaction.response.send_message(
            "✅ Doğrulama işleminiz başarıyla tamamlandı!", 
            ephemeral=True
        )


class VerifyKur(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="verify-kur", 
        description="Sunucu için güvenli doğrulama panelini kurar."
    )
    @app_commands.default_permissions(administrator=True) # Sadece Yöneticiler
    @app_commands.guild_only() # Sadece sunucularda çalışır (DM dışı)
    async def verify_kur(self, interaction: discord.Interaction):
        
        # Şık bir doğrulama embed tasarımı
        embed = discord.Embed(
            title="🛡️ Sunucu Doğrulama Sistemi",
            description="Sunucudaki diğer kanallara erişim sağlamak ve topluluğumuza katılmak için aşağıdaki **Doğrula** butonuna tıklayın.",
            color=discord.Color.from_str("#00ffcc")
        )
        
        # Sunucu simgesi varsa ekle
        guild_icon = interaction.guild.icon.url if interaction.guild.icon else None
        embed.set_footer(
            text=f"{interaction.guild.name} Güvenlik Sistemi", 
            icon_url=guild_icon
        )
        embed.timestamp = interaction.created_at

        # Görünümü (Butonu) ekliyoruz
        view = VerifyView()

        # Komutu kullanan kişiye gizli (ephemeral) yanıt veriyoruz
        await interaction.response.send_message(
            "⚙️ Doğrulama paneli başarıyla oluşturuldu.", 
            ephemeral=True
        )
        
        # Kanala embed mesajını ve butonu gönderiyoruz
        await interaction.channel.send(embed=embed, view=view)


# Cog yükleme fonksiyonu
async def setup(bot: commands.Bot):
    await bot.add_cog(VerifyKur(bot))
