from discord import app_commands

from core.economy import deposit as deposit_money
from core.economy import format_money
from core.embeds import make_embed


def register(bot):
    @bot.tree.command(name="deposit", description="Cuzdandaki parayi bankaya yatirir.")
    @app_commands.guild_only()
    async def deposit(interaction, amount: app_commands.Range[int, 1, 1000000000]):
        success, account = deposit_money(interaction.guild.id, interaction.user.id, amount)

        if not success:
            await interaction.response.send_message(
                embed=make_embed("Yetersiz bakiye", f"Cuzdaninda sadece {format_money(account['wallet'])} var.", 0xE74C3C),
                ephemeral=True
            )
            return

        embed = make_embed("Para yatirildi", f"Bankaya {format_money(amount)} yatirdin.", 0x2ECC71)
        embed.add_field(name="Cuzdan", value=format_money(account["wallet"]), inline=True)
        embed.add_field(name="Banka", value=format_money(account["bank"]), inline=True)
        await interaction.response.send_message(embed=embed)
