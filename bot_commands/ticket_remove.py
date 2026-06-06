import discord
from discord import app_commands

from core.embeds import make_embed
from core.logging import log_event
from core.storage import get_ticket_record, remove_ticket_user
from core.tickets import is_ticket_staff


def register(bot):
    @bot.tree.command(name="ticket-remove", description="Ticketten uye cikarir.")
    @app_commands.guild_only()
    @app_commands.default_permissions(send_messages=True)
    @app_commands.checks.bot_has_permissions(manage_channels=True, embed_links=True)
    async def ticket_remove(interaction, member: discord.Member):
        ticket = get_ticket_record(interaction.guild.id, interaction.channel.id)
        if not ticket or ticket.get("status") != "open":
            await interaction.response.send_message(
                embed=make_embed("Ticket Bulunamadi", "Bu kanal acik bir ticket degil.", 0xE74C3C),
                ephemeral=True
            )
            return
        if member.id == int(ticket["owner_id"]):
            await interaction.response.send_message(
                embed=make_embed("Islem Reddedildi", "Ticket sahibini ticketten cikaramazsin.", 0xE74C3C),
                ephemeral=True
            )
            return
        if not is_ticket_staff(interaction.user):
            await interaction.response.send_message(
                embed=make_embed("Yetki Reddedildi", "Bu komut ticket yetkilileri icindir.", 0xE74C3C),
                ephemeral=True
            )
            return

        await interaction.channel.set_permissions(member, overwrite=None)
        remove_ticket_user(interaction.guild.id, interaction.channel.id, member.id)
        await interaction.response.send_message(
            embed=make_embed("Uye Cikarildi", f"{member.mention} ticketten cikarildi.", 0xE67E22)
        )
        await log_event(
            interaction.guild,
            "Ticket Uye Cikarildi",
            f"{member} ticketten cikarildi.",
            0xE67E22,
            [
                ("Yetkili", f"{interaction.user} ({interaction.user.id})"),
                ("Uye", f"{member} ({member.id})"),
                ("Kanal", f"{interaction.channel} ({interaction.channel_id})")
            ]
        )
