import discord
from discord import app_commands

from core.economy import format_money, remove_money
from core.embeds import make_embed
from core.logging import log_event


def register(bot):
    @bot.tree.command(name="eco-remove", description="Yetkili olarak uyeden ekonomi kredisi siler.")
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.bot_has_permissions(embed_links=True)
    @app_commands.choices(target=[
        app_commands.Choice(name="Cuzdan", value="wallet"),
        app_commands.Choice(name="Banka", value="bank")
    ])
    async def eco_remove(
        interaction,
        member: discord.Member,
        amount: app_commands.Range[int, 1, 1000000000],
        target: app_commands.Choice[str],
        reason: str = "Sebep belirtilmedi"
    ):
        removed, account = remove_money(interaction.guild.id, member.id, amount, target.value)
        embed = make_embed("Ekonomi Guncellendi", f"{member.mention} hesabindan {format_money(removed)} silindi.", 0xE67E22)
        embed.add_field(name="Cuzdan", value=format_money(account["wallet"]), inline=True)
        embed.add_field(name="Banka", value=format_money(account["bank"]), inline=True)
        embed.add_field(name="Sebep", value=reason, inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await log_event(
            interaction.guild,
            "Eco Remove",
            f"{member} hesabindan {format_money(removed)} silindi.",
            0xE67E22,
            [
                ("Yetkili", f"{interaction.user} ({interaction.user.id})"),
                ("Uye", f"{member} ({member.id})"),
                ("Hedef", target.name),
                ("Sebep", reason)
            ]
        )
