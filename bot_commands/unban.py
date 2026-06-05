from discord import app_commands

from core.embeds import make_embed
from core.logging import log_event


def register(bot):
    @bot.tree.command(name="unban", description="ID ile ban kaldirir.")
    @app_commands.guild_only()
    @app_commands.default_permissions(ban_members=True)
    @app_commands.checks.bot_has_permissions(ban_members=True, embed_links=True)
    async def unban(interaction, user_id: str, reason: str = "Sebep belirtilmedi"):
        user = await bot.fetch_user(int(user_id))
        await interaction.guild.unban(user, reason=reason)
        await interaction.response.send_message(
            embed=make_embed("Ban kaldirildi", f"{user} bani kaldirildi.", 0x2ECC71)
        )
        await log_event(
            interaction.guild,
            "Moderasyon: Unban",
            f"{user} bani kaldirildi.",
            0x2ECC71,
            [
                ("Yetkili", f"{interaction.user} ({interaction.user.id})"),
                ("Kullanici", f"{user} ({user.id})"),
                ("Sebep", reason)
            ]
        )
