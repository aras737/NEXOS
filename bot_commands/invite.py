from discord import app_commands

from core.embeds import make_embed
from core.permissions import REQUIRED_PERMISSION_LABELS, invite_url, required_permissions


def register(bot):
    @bot.tree.command(name="invite", description="Bot davet linkini ve gerekli yetkileri gosterir.")
    @app_commands.guild_only()
    async def invite(interaction):
        client_id = interaction.client.user.id
        url = invite_url(client_id)
        permissions = required_permissions().value
        labels = "\n".join(f"- {label}" for label in REQUIRED_PERMISSION_LABELS)

        embed = make_embed(
            "NEXOS Davet ve Yetkiler",
            f"[Botu yetkili davet et]({url})\n\nPermission bit: `{permissions}`",
            0x5865F2
        )
        embed.add_field(name="Gerekli Yetkiler", value=labels, inline=False)
        embed.set_footer(text="Uye sayaci icin Manage Channels yetkisi gerekir.")
        await interaction.response.send_message(embed=embed, ephemeral=True)
