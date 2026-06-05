import discord
from discord import app_commands

from core.embeds import make_embed
from core.logging import log_event
from core.storage import set_guild_setting
from core.tickets import TicketPanelView


def register(bot):
    @bot.tree.command(name="ticket-panel", description="Ticket paneli gonderir.")
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.bot_has_permissions(send_messages=True, embed_links=True, manage_channels=True)
    async def ticket_panel(
        interaction,
        channel: discord.TextChannel | None = None,
        support_role: discord.Role | None = None
    ):
        target_channel = channel or interaction.channel
        if support_role:
            set_guild_setting(interaction.guild.id, "ticket_support_role_id", support_role.id)

        embed = make_embed(
            "NEXOS Destek",
            "Destek almak icin asagidaki butona bas. Ticket kanali sadece sen ve yetkililer tarafindan gorulur.",
            0x5865F2
        )
        embed.set_footer(text="Gereksiz ticket acmak moderasyon islemine sebep olabilir.")
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
                ("Destek Rolu", support_role.mention if support_role else "Ayarlanmadi")
            ]
        )
