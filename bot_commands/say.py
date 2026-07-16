from discord import app_commands

from core.embeds import make_embed
from core.logging import log_event

# Buraya komutu kullanmasını istediğin kişilerin Discord ID'lerini ekleyebilirsin.
# Birden fazla ID eklemek istersen virgülle ayırabilirsin: [1234567890, 9876543210]
ALLOWED_IDS = [1389930042200559706] 


def register(bot):
    @bot.tree.command(name="say", description="Bot adina mesaj gonderir.")
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.bot_has_permissions(send_messages=True, embed_links=True)
    async def say(interaction, message: app_commands.Range[str, 1, 1900]):
        # Kullanıcı hem sunucu sahibi değilse HEM DE izin verilen ID listesinde yoksa engelle
        if interaction.user.id != interaction.guild.owner_id and interaction.user.id not in ALLOWED_IDS:
            await interaction.response.send_message(
                embed=make_embed("Yetki reddedildi", "Bu komutu sadece sunucu sahibi veya yetkili kişiler kullanabilir.", 0xE74C3C),
                ephemeral=True
            )
            await log_event(
                interaction.guild,
                "Say Reddedildi",
                "/say komutu yetkisiz bir kullanıcı tarafından kullanılmaya çalışıldı.",
                0xE74C3C,
                [("Kullanan", f"{interaction.user} ({interaction.user.id})")]
            )
            return

        await interaction.response.defer(ephemeral=True)
        await interaction.channel.send(message)
        await interaction.followup.send("Gonderildi.", ephemeral=True)
        await log_event(
            interaction.guild,
            "Say Kullanildi",
            f"{interaction.user} bot adina mesaj gonderdi.",
            0x2ECC71,
            [
                ("Kanal", f"{interaction.channel} ({interaction.channel_id})"),
                ("Mesaj", message)
            ]
        )
