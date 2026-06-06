from discord import app_commands

from core.embeds import make_embed
from core.logging import log_event
from core.storage import get_ticket_record
from core.tickets import is_ticket_staff


def clean_name(name):
    cleaned = "".join(char.lower() if char.isalnum() else "-" for char in name)
    cleaned = "-".join(part for part in cleaned.split("-") if part)
    return f"ticket-{cleaned[:80]}"


def register(bot):
    @bot.tree.command(name="ticket-rename", description="Ticket kanalinin adini degistirir.")
    @app_commands.guild_only()
    @app_commands.default_permissions(send_messages=True)
    @app_commands.checks.bot_has_permissions(manage_channels=True, embed_links=True)
    async def ticket_rename(interaction, name: app_commands.Range[str, 3, 80]):
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

        old_name = interaction.channel.name
        new_name = clean_name(name)
        await interaction.channel.edit(name=new_name, reason=f"NEXOS ticket rename: {interaction.user}")
        await interaction.response.send_message(
            embed=make_embed("Ticket Adi Degisti", f"`{old_name}` -> `{new_name}`", 0x2ECC71),
            ephemeral=True
        )
        await log_event(
            interaction.guild,
            "Ticket Rename",
            f"{old_name} ticket adi {new_name} olarak degisti.",
            0x3498DB,
            [("Yetkili", f"{interaction.user} ({interaction.user.id})")]
        )
