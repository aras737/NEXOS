from discord import app_commands

from core.embeds import make_embed
from core.storage import get_ticket_record
from core.tickets import PRIORITY_COLORS, PRIORITY_LABELS


def register(bot):
    @bot.tree.command(name="ticket-info", description="Bulundugun ticket hakkinda bilgi verir.")
    @app_commands.guild_only()
    @app_commands.default_permissions(send_messages=True)
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def ticket_info(interaction):
        ticket = get_ticket_record(interaction.guild.id, interaction.channel.id)
        if not ticket:
            await interaction.response.send_message(
                embed=make_embed("Ticket Bulunamadi", "Bu kanal NEXOS ticket kaydina sahip degil.", 0xE74C3C),
                ephemeral=True
            )
            return

        priority = ticket.get("priority", "normal")
        owner = interaction.guild.get_member(int(ticket["owner_id"]))
        claimed_by = ticket.get("claimed_by")
        claimed_member = interaction.guild.get_member(int(claimed_by)) if claimed_by else None
        added = ticket.get("added_users", [])
        added_text = ", ".join(f"<@{user_id}>" for user_id in added) if added else "Yok"

        embed = make_embed("Ticket Bilgisi", ticket.get("subject", "Konu yok"), PRIORITY_COLORS.get(priority, 0x5865F2))
        embed.add_field(name="Sahip", value=owner.mention if owner else ticket["owner_id"], inline=True)
        embed.add_field(name="Durum", value=ticket.get("status", "bilinmiyor"), inline=True)
        embed.add_field(name="Oncelik", value=PRIORITY_LABELS.get(priority, priority), inline=True)
        embed.add_field(name="Ustlenen", value=claimed_member.mention if claimed_member else "Yok", inline=True)
        embed.add_field(name="Eklenen Uyeler", value=added_text, inline=False)
        embed.add_field(name="Detay", value=ticket.get("details") or "Yok", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)
