from discord import app_commands

from core.tickets import create_ticket


def register(bot):
    @bot.tree.command(name="ticket-open", description="Kendin icin ticket acar.")
    @app_commands.guild_only()
    @app_commands.default_permissions(send_messages=True)
    @app_commands.checks.bot_has_permissions(send_messages=True, embed_links=True, manage_channels=True)
    async def ticket_open(interaction, subject: app_commands.Range[str, 3, 120]):
        await create_ticket(interaction, subject)
