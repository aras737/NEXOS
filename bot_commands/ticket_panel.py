import discord
from discord import app_commands

from core.embeds import make_embed
from core.logging import log_event
from core.storage import set_guild_setting
from core.tickets import PANEL_COLOR, TicketPanelView


def register(bot):
    @bot.tree.command(name="ticket-panel", description="Panel-only ticket sistemini gonderir.")
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.bot_has_permissions(send_messages=True, embed_links=True, manage_channels=True)
    async def ticket_panel(
        interaction,
        channel: discord.TextChannel | None = None,
        support_role: discord.Role | None = None,
        category: discord.CategoryChannel | None = None
    ):
        target_channel = channel or interaction.channel
        if support_role:
            set_guild_setting(interaction.guild.id, "ticket_support_role_id", support_role.id)
        if category:
            set_guild_setting(interaction.guild.id, "ticket_category_id", category.id)

        embed = make_embed(
            "NEXOS Ticket Paneli",
            "Destek almak icin **Ticket Ac** butonuna bas. Ticketler sadece bu panelden acilir; kanal sadece ticket sahibi ve yetkililer tarafindan gorulur.",
            PANEL_COLOR
        )
        embed.add_field(
            name="Ticket Icinde",
            value="Ustlenme, oncelik, uye ekleme/cikarma, yeniden adlandirma, bilgi, transcript ve kapatma kontrolleri otomatik gelir.",
            inline=False
        )
        embed.add_field(
            name="Yetkili Erisimi",
            value=support_role.mention if support_role else "Mevcut yetkili rol ayari korunur.",
            inline=True
        )
        embed.add_field(
            name="Kategori",
            value=category.name if category else "Mevcut kategori ayari korunur.",
            inline=True
        )
        embed.set_footer(text="Diger ticket komutlari yok; tum ticket islemleri panel ve kanal kontrollerinden yapilir.")
        await target_channel.send(embed=embed, view=TicketPanelView())
        await interaction.response.send_message(
            embed=make_embed("Ticket Paneli Gonderildi", f"Panel {target_channel.mention} kanalina gonderildi.", 0x2ECC71),
            ephemeral=True
        )
        await log_event(
            interaction.guild,
            "Ticket Paneli Gonderildi",
            f"Ticket paneli {target_channel.mention} kanalina gonderildi.",
            0x2ECC71,
            [
                ("Yetkili", f"{interaction.user} ({interaction.user.id})"),
                ("Destek Rolu", support_role.mention if support_role else "Degismedi"),
                ("Kategori", category.name if category else "Degismedi")
            ]
        )
