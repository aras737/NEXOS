import discord
from discord import app_commands

from core.economy import format_money, get_account, get_rank
from core.embeds import make_embed
from core.storage import get_warnings


def register(bot):
    @bot.tree.command(name="profile", description="Uyenin NEXOS profil kartini gosterir.")
    @app_commands.guild_only()
    @app_commands.default_permissions(send_messages=True)
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def profile(interaction, member: discord.Member | None = None):
        member = member or interaction.user
        account = get_account(interaction.guild.id, member.id)
        warnings = get_warnings(interaction.guild.id, member.id)
        total = account["wallet"] + account["bank"]
        rank = get_rank(interaction.guild.id, member.id)

        embed = make_embed(member.display_name, "NEXOS profil karti", 0x9B5DE5)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Cuzdan", value=format_money(account["wallet"]), inline=True)
        embed.add_field(name="Banka", value=format_money(account["bank"]), inline=True)
        embed.add_field(name="Toplam", value=format_money(total), inline=True)
        embed.add_field(name="Ekonomi Sirasi", value=f"#{rank}" if rank else "Liste disi", inline=True)
        embed.add_field(name="Uyari", value=str(len(warnings)), inline=True)
        embed.add_field(name="Roller", value=str(len(member.roles) - 1), inline=True)
        embed.add_field(name="Hesap", value=discord.utils.format_dt(member.created_at, "R"), inline=True)
        embed.add_field(name="Katilim", value=discord.utils.format_dt(member.joined_at, "R"), inline=True)
        embed.set_footer(text=f"ID: {member.id}")
        await interaction.response.send_message(embed=embed)
