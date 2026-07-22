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
        interaction: discord.Interaction,
        channel: discord.TextChannel | None = None,
        category: discord.CategoryChannel | None = None,
        support_role_1: discord.Role | None = None,
        support_role_2: discord.Role | None = None,
        support_role_3: discord.Role | None = None,
    ):
        target_channel = channel or interaction.channel
        
        # Seçilen rolleri bir listede topla (boş olmayanları al)
        roles = [r for r in [support_role_1, support_role_2, support_role_3] if r is not None]
        
        if roles:
            # Roller ID listesi olarak kaydedilir (Örn: [123456789, 987654321])
            role_ids = [role.id for role in roles]
            set_guild_setting(interaction.guild.id, "ticket_support_role_ids", role_ids)

        embed = make_embed(
            "AETHELGARD Ticket Paneli",
            "Destek almak icin **Ticket Ac** butonuna bas. Ticketler sadece bu panelden acilir; kanal sadece ticket sahibi ve yetkililer tarafindan gorulur.",
            PANEL_COLOR
        )
        embed.add_field(
            name="Ticket Icinde",
            value="Ustlenme, oncelik, uye ekleme/cikarma, yeniden adlandirma, bilgi, transcript ve kapatma kontrolleri otomatik gelir.",
            inline=False
        )
        
        # Eklenen rolleri panele yazdır
        roles_text = ", ".join([role.mention for role in roles]) if roles else "Mevcut yetkili rol ayarlari korunur."
        embed.add_field(
            name="Yetkili Rolleri",
            value=roles_text,
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
        
        log_roles_text = ", ".join([f"{role.name} ({role.id})" for role in roles]) if roles else "Degismedi"
        await log_event(
            interaction.guild,
            "Ticket Paneli Gonderildi",
            f"Ticket paneli {target_channel.mention} kanalina gonderildi.",
            0x2ECC71,
            [
                ("Yetkili", f"{interaction.user} ({interaction.user.id})"),
                ("Destek Rolleri", log_roles_text),
                ("Kategori", category.name if category else "Degismedi")
            ]
        )
