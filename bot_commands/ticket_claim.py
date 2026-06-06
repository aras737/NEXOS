from discord import app_commands

from core.embeds import make_embed
from core.logging import log_event
from core.storage import get_ticket_record, update_ticket_record
from core.tickets import is_ticket_staff


def register(bot):
    @bot.tree.command(name="ticket-claim", description="Bulundugun ticketi ustlenir.")
    @app_commands.guild_only()
    @app_commands.default_permissions(send_messages=True)
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def ticket_claim(interaction):
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

        update_ticket_record(interaction.guild.id, interaction.channel.id, claimed_by=interaction.user.id)
        await interaction.response.send_message(
            embed=make_embed("Ticket Ustlenildi", f"{interaction.user.mention} bu ticketi ustlendi.", 0x2ECC71)
        )
        await log_event(
            interaction.guild,
            "Ticket Claim",
            f"{interaction.channel} ticketi ustlenildi.",
            0x2ECC71,
            [("Yetkili", f"{interaction.user} ({interaction.user.id})")]
        )
