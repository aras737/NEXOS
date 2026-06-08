from discord import app_commands

from core.embeds import make_embed
from core.logging import LOG_TYPE_LABELS, trim
from core.storage import get_last_actions


LOG_TYPE_CHOICES = [
    app_commands.Choice(name=label, value=key)
    for key, label in LOG_TYPE_LABELS.items()
]


def format_action(action):
    if not action:
        return "Kayit yok."

    fields = action.get("fields", [])
    preview = []
    for item in fields[:3]:
        preview.append(f"**{item.get('name')}**: {trim(item.get('value'), 120)}")
    details = "\n".join(preview) if preview else "Detay yok."
    return (
        f"**{action.get('title', 'Bilinmiyor')}**\n"
        f"{trim(action.get('description', 'Aciklama yok.'), 240)}\n"
        f"`{action.get('created_at', 'tarih yok')}`\n"
        f"{details}"
    )


def register(bot):
    @bot.tree.command(name="last-actions", description="Botun kaydettigi son islemleri gosterir.")
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.bot_has_permissions(embed_links=True)
    @app_commands.choices(log_type=LOG_TYPE_CHOICES)
    async def last_actions(interaction, log_type: app_commands.Choice[str] | None = None):
        actions = get_last_actions(interaction.guild.id)

        if log_type:
            selected = actions.get(log_type.value)
            embed = make_embed(
                f"Son Islem: {LOG_TYPE_LABELS[log_type.value]}",
                format_action(selected),
                0x8B5CF6
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        embed = make_embed(
            "NEXOS Son Islemler",
            format_action(actions.get("_all")),
            0x8B5CF6
        )
        for key, label in LOG_TYPE_LABELS.items():
            embed.add_field(name=label, value=format_action(actions.get(key)), inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)
