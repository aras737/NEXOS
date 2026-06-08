import discord
from discord import app_commands

from core.embeds import make_embed
from core.logging import LOG_TYPE_LABELS, log_event, set_log_channel_setting


LOG_TYPE_CHOICES = [
    app_commands.Choice(name=label, value=key)
    for key, label in LOG_TYPE_LABELS.items()
]


def register(bot):
    @bot.tree.command(name="set-log-channel", description="Log kanalini veya ozel log turu kanalini ayarlar.")
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.bot_has_permissions(embed_links=True, send_messages=True)
    @app_commands.choices(log_type=LOG_TYPE_CHOICES)
    async def set_log_channel(
        interaction,
        channel: discord.TextChannel,
        log_type: app_commands.Choice[str] | None = None
    ):
        selected_type = log_type.value if log_type else "general"
        set_log_channel_setting(interaction.guild.id, selected_type, channel.id)
        type_label = LOG_TYPE_LABELS[selected_type]

        await interaction.response.send_message(
            embed=make_embed(
                "Log Kanali Ayarlandi",
                f"**{type_label}** artik {channel.mention} kanalina gonderilecek.",
                0x2ECC71
            ),
            ephemeral=True
        )
        await log_event(
            interaction.guild,
            "Log Kanali Ayarlandi",
            f"{type_label}: {channel.mention}",
            0x2ECC71,
            [
                ("Yetkili", f"{interaction.user} ({interaction.user.id})"),
                ("Log Turu", type_label),
                ("Kanal", f"{channel} ({channel.id})")
            ],
            log_type="general"
        )
