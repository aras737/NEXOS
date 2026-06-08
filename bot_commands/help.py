from discord import app_commands

from core.embeds import make_embed
from core.emojis import with_emoji


COMMAND_LINES = [
    "`/help` komut listesini gosterir.",
    "`/invite` bot davet linkini ve gerekli yetkileri gosterir.",
    "`/set-log-channel` log kanalini ayarlar.",
    "`/set-auto-role` yeni gelenlere otomatik rol ayarlar.",
    "`/welcome-settings` giris-cikis kanali ve galaksi mesajlarini ayarlar.",
    "`/role-panel` butona tiklayanlara rol veren paneli gonderir.",
    "`/ping` bot gecikmesini gosterir.",
    "`/server` sunucu bilgilerini gosterir.",
    "`/user` uye bilgilerini gosterir.",
    "`/profile` ozel NEXOS profil kartini gosterir.",
    "`/avatar` uye avatarini gosterir.",
    "`/botinfo` bot sistem bilgisini gosterir.",
    "`/balance` ekonomi bakiyesini gosterir.",
    "`/daily` gunluk odul alir.",
    "`/work` calisip kredi kazanir.",
    "`/deposit` cuzdandan bankaya para yatirir.",
    "`/withdraw` bankadan cuzdana para ceker.",
    "`/pay` baska uyeye para gonderir.",
    "`/leaderboard` ekonomi liderlerini gosterir.",
    "`/eco-add` yetkili olarak kredi ekler.",
    "`/eco-remove` yetkili olarak kredi siler.",
    "`/eco-set` yetkili olarak bakiyeyi ayarlar.",
    "`/eco-reset` yetkili olarak ekonomi hesabini sifirlar.",
    "`/ticket-panel` panel-only ticket sistemini gonderir; diger ticket islemleri butonlardan yapilir.",
    "`/clear` mesaj siler.",
    "`/kick` uyeyi atar.",
    "`/ban` uyeyi banlar.",
    "`/unban` ban kaldirir.",
    "`/timeout` uyeyi susturur.",
    "`/untimeout` susturmayi kaldirir.",
    "`/warn` uyari verir.",
    "`/warnings` uyarilari listeler.",
    "`/clear-warnings` uyarilari temizler.",
    "`/role-add` rol verir.",
    "`/role-remove` rol alir.",
    "`/lock` kanali kilitler.",
    "`/unlock` kanal kilidini acar.",
    "`/slowmode` yavas modu ayarlar.",
    "`/say` bot adina mesaj gonderir. Sadece sunucu sahibi.",
    "`/embed` embed mesaj gonderir.",
    "`/kurulum` temel kanal kurulumunu yapar."
]


def register(bot):
    @bot.tree.command(name="help", description="Komut listesini gosterir.")
    @app_commands.guild_only()
    @app_commands.default_permissions(send_messages=True)
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def help_command(interaction):
        await interaction.response.send_message(
            embed=make_embed(with_emoji("bot", "NEXOS Slash Komutlari"), "\n".join(COMMAND_LINES), 0x8B5CF6),
            ephemeral=True
        )
