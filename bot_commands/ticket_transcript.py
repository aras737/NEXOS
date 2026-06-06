import discord
from discord import app_commands

from core.embeds import make_embed
from core.logging import log_event
from core.storage import get_ticket_record, transcript_path
from core.tickets import is_ticket_staff


async def build_transcript(channel, limit):
    lines = []
    async for message in channel.history(limit=limit, oldest_first=True):
        created_at = message.created_at.isoformat()
        attachments = " ".join(attachment.url for attachment in message.attachments)
        content = message.content or ""
        if attachments:
            content = f"{content} {attachments}".strip()
        if message.embeds and not content:
            content = "[embed mesaj]"
        lines.append(f"[{created_at}] {message.author} ({message.author.id}): {content}")
    return "\n".join(lines) or "Transcript icin mesaj bulunamadi."


def register(bot):
    @bot.tree.command(name="ticket-transcript", description="Ticket mesaj dokumunu olusturur.")
    @app_commands.guild_only()
    @app_commands.default_permissions(send_messages=True)
    @app_commands.checks.bot_has_permissions(read_message_history=True, attach_files=True, embed_links=True)
    async def ticket_transcript(interaction, limit: app_commands.Range[int, 10, 1000] = 300):
        ticket = get_ticket_record(interaction.guild.id, interaction.channel.id)
        if not ticket:
            await interaction.response.send_message(
                embed=make_embed("Ticket Bulunamadi", "Bu kanal NEXOS ticket kaydina sahip degil.", 0xE74C3C),
                ephemeral=True
            )
            return
        is_owner = interaction.user.id == int(ticket["owner_id"])
        if not is_owner and not is_ticket_staff(interaction.user):
            await interaction.response.send_message(
                embed=make_embed("Yetki Reddedildi", "Transcript icin ticket sahibi veya ticket yetkilisi olmalisin.", 0xE74C3C),
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)
        content = await build_transcript(interaction.channel, limit)
        path = transcript_path(interaction.guild.id, interaction.channel.id)
        path.write_text(content, encoding="utf-8")
        await interaction.followup.send(
            embed=make_embed("Transcript Hazir", f"Son {limit} mesaj icin transcript olusturuldu.", 0x2ECC71),
            file=discord.File(path)
        )
        await log_event(
            interaction.guild,
            "Ticket Transcript",
            f"{interaction.channel} icin transcript olusturuldu.",
            0x3498DB,
            [
                ("Olusturan", f"{interaction.user} ({interaction.user.id})"),
                ("Limit", limit),
                ("Dosya", str(path))
            ]
        )
