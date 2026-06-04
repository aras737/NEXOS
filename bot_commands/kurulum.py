from discord import app_commands


def register(bot):
    @bot.tree.command(name="kurulum", description="Temel sunucu kanal kurulumunu yapar.")
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    async def kurulum(interaction):
        guild = interaction.guild
        await interaction.response.defer(thinking=True, ephemeral=True)

        info_category = await guild.create_category("BILGI MERKEZI")
        await guild.create_text_channel("kurallar", category=info_category)
        await guild.create_text_channel("duyurular", category=info_category)
        await guild.create_text_channel("rol-al", category=info_category)

        lobby_category = await guild.create_category("SOHBET")
        await guild.create_text_channel("genel-sohbet", category=lobby_category)
        await guild.create_text_channel("bot-komut", category=lobby_category)
        await guild.create_text_channel("medya", category=lobby_category)

        voice_category = await guild.create_category("SES KANALLARI")
        await guild.create_voice_channel("Genel Ses", category=voice_category)
        await guild.create_voice_channel("Duo #1", category=voice_category, user_limit=2)
        await guild.create_voice_channel("Squad #1", category=voice_category, user_limit=5)
        await guild.create_voice_channel("AFK", category=voice_category)

        await interaction.followup.send("NEXOS kurulumu basariyla tamamlandi.", ephemeral=True)
