from discord import app_commands

from core.embeds import make_embed
from core.logging import log_event
from core.storage import get_ticket_record, update_ticket_record
from core.tickets import PRIORITY_COLORS, PRIORITY_LABELS, is_ticket_staff


def register(bot):
    @bot.tree.command(name="ticket-priority", description="Ticket onceligini degistirir.")
    @app_commands.guild_only()
    @app_commands.default_permissions(send_messages=True)
    @app_commands.checks.bot_has_permissions(embed_links=True)
    @app_commands.choices(priority=[
        app_commands.Choice(name="Dusuk", value="dusuk"),
        app_commands.Choice(name="Normal", value="normal"),
        app_commands.Choice(name="Yuksek", value="yuksek"),
        app_commands.Choice(name="Acil", value="acil")
    ])
    async def ticket_priority(interaction, priority: app_commands.Choice[str]):
        ticket = get_ticket_record(interaction.guild.id, interaction.channel.id)
        if not ticket or ticket.get("status") != "open":
            await interaction.response.send_message(
                embed=make_embed("Ticket Bulunamadi", "Bu kanal acik bir ticket degil.", 0xE74C3C),
                ephemeral=True
            )
            return
        if not is_ticket_staff(interaction.user):
            await interaction.response.send_message(
                embed=make_embed("Yetki Reddedildi", "Bu komut ticket yetkilileri icindir.", 0xE74C3C),
                ephemeral=True
            )
            return

        update_ticket_record(interaction.guild.id, interaction.channel.id, priority=priority.value)
        await interaction.response.send_message(
            embed=make_embed("Oncelik Guncellendi", f"Ticket onceligi: **{PRIORITY_LABELS[priority.value]}**", PRIORITY_COLORS[priority.value])
        )
        await log_event(
            interaction.guild,
            "Ticket Oncelik",
            f"{interaction.channel} onceligi {PRIORITY_LABELS[priority.value]} yapildi.",
            PRIORITY_COLORS[priority.value],
            [("Yetkili", f"{interaction.user} ({interaction.user.id})")]
        )
