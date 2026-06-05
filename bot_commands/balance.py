import discord
from discord import app_commands

from core.economy import format_money, get_account, get_rank
from core.embeds import make_embed


def register(bot):
    @bot.tree.command(name="balance", description="Ekonomi bakiyesini gosterir.")
    @app_commands.guild_only()
    async def balance(interaction, member: discord.Member | None = None):
        member = member or interaction.user
        account = get_account(interaction.guild.id, member.id)
        wallet = account["wallet"]
        bank = account["bank"]
        total = wallet + bank
        rank = get_rank(interaction.guild.id, member.id)

        embed = make_embed(str(member), "NEXOS ekonomi profili", 0xF1C40F)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Cuzdan", value=format_money(wallet), inline=True)
        embed.add_field(name="Banka", value=format_money(bank), inline=True)
        embed.add_field(name="Toplam", value=format_money(total), inline=True)
        embed.add_field(name="Siralama", value=f"#{rank}" if rank else "Liste disi", inline=True)
        embed.set_footer(text="NEXOS Economy")
        await interaction.response.send_message(embed=embed)
