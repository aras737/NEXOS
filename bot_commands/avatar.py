import discord
from discord import app_commands

from core.embeds import make_embed


def register(bot):
    @bot.tree.command(name="avatar", description="Uyenin avatarini gosterir.")
    @app_commands.guild_only()
    @app_commands.default_permissions(send_messages=True)
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def avatar(interaction, member: discord.Member | None = None):
        member = member or interaction.user
        avatar_url = member.display_avatar.url
        embed = make_embed(str(member), f"[Avatar linki]({avatar_url})", 0x5865F2)
        embed.set_image(url=avatar_url)
        await interaction.response.send_message(embed=embed)
