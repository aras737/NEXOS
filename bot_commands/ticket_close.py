import asyncio

import discord
from discord import app_commands

from core.embeds import make_embed
from core.logging import log_event
from core.storage import close_ticket_record, get_ticket_record


async def close_ticket_channel(interaction, reason="Sebep belirtilmedi"):
    ticket = get_ticket_record(interaction.guild.id, interaction.channel.id)
    if not ticket or ticket.get("status") != "open":
        await interaction.response.send_message(
            embed=make_embed("Ticket Bulunamadi", "Bu kanal acik bir NEXOS ticket kanali degil.", 0xE74C3C),
            ephemeral=True
        )
        return

    is_owner = interaction.user.id == int(ticket["owner_id"])
    has_manage_channels = interaction.user.guild_permissions.manage_channels
    if not is_owner and not has_manage_channels:
        await interaction.response.send_message(
            embed=make_embed("Yetki Reddedildi", "Bu ticketi sadece ticket sahibi veya kanal yoneticileri kapatabilir.", 0xE74C3C),
            ephemeral=True
        )
        return

    close_ticket_record(interaction.guild.id, interaction.channel.id)
    await interaction.response.send_message(
        embed=make_embed("Ticket Kapatiliyor", f"Ticket 3 saniye icinde kapatilacak.\nSebep: {reason}", 0xE67E22),
        ephemeral=True
    )
    await log_event(
        interaction.guild,
        "Ticket Kapatildi",
        f"{interaction.channel} ticketi kapatildi.",
        0xE67E22,
        [
            ("Kapatan", f"{interaction.user} ({interaction.user.id})"),
            ("Ticket Sahibi", ticket["owner_id"]),
            ("Sebep", reason)
        ]
    )
    await asyncio.sleep(3)
    await interaction.channel.delete(reason=f"NEXOS ticket kapatildi: {reason}")


def register(bot):
    @bot.tree.command(name="ticket-close", description="Bulundugun ticket kanalini kapatir.")
    @app_commands.guild_only()
    @app_commands.default_permissions(send_messages=True)
    @app_commands.checks.bot_has_permissions(manage_channels=True, send_messages=True, embed_links=True)
    async def ticket_close(interaction, reason: str = "Sebep belirtilmedi"):
        await close_ticket_channel(interaction, reason)
