from discord import app_commands

from core.embeds import make_embed


COMMAND_LINES = [
    "`/help` komut listesini gosterir.",
    "`/invite` bot davet linkini ve gerekli yetkileri gosterir.",
    "`/set-log-channel` log kanalini ayarlar.",
    "`/ping` bot gecikmesini gosterir.",
    "`/server` sunucu bilgilerini gosterir.",
    "`/user` uye bilgilerini gosterir.",
    "`/balance` ekonomi bakiyesini gosterir.",
    "`/daily` gunluk odul alir.",
    "`/work` calisip kredi kazanir.",
    "`/deposit` cuzdandan bankaya para yatirir.",
    "`/withdraw` bankadan cuzdana para ceker.",
    "`/pay` baska uyeye para gonderir.",
    "`/leaderboard` ekonomi liderlerini gosterir.",
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
            embed=make_embed("NEXOS Slash Komutlari", "\n".join(COMMAND_LINES)),
            ephemeral=True
        )
