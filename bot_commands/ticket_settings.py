import discord
from discord import app_commands

from core.embeds import make_embed
from core.logging import log_event
from core.storage import set_guild_setting


def register(bot):
    @bot.tree.command(name="ticket-settings", description="Ticket kategori ve yetkili rol ayarlarini yapar.")
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def ticket_settings(
        interaction,
        support_role: discord.Role | None = None,
        category: discord.CategoryChannel | None = None
    ):
        if support_role:
            set_guild_setting(interaction.guild.id, "ticket_support_role_id", support_role.id)
        if category:
            set_guild_setting(interaction.guild.id, "ticket_category_id", category.id)

        embed = make_embed("Ticket Ayarlari", "Ticket sistemi ayarlari guncellendi.", 0x2ECC71)
        embed.add_field(name="Yetkili Rol", value=support_role.mention if support_role else "Degismedi", inline=True)
        embed.add_field(name="Kategori", value=category.name if category else "Degismedi", inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await log_event(
            interaction.guild,
            "Ticket Ayarlari",
            "Ticket ayarlari guncellendi.",
            0x2ECC71,
            [
                ("Yetkili", f"{interaction.user} ({interaction.user.id})"),
                ("Destek Rolu", support_role.mention if support_role else "Degismedi"),
                ("Kategori", category.name if category else "Degismedi")
            ]
        )
