from discord import app_commands

from core.economy import format_money
from core.economy import withdraw as withdraw_money
from core.embeds import make_embed


def register(bot):
    @bot.tree.command(name="withdraw", description="Bankadaki parayi cuzdanina ceker.")
    @app_commands.guild_only()
    async def withdraw(interaction, amount: app_commands.Range[int, 1, 1000000000]):
        success, account = withdraw_money(interaction.guild.id, interaction.user.id, amount)

        if not success:
            await interaction.response.send_message(
                embed=make_embed("Yetersiz banka bakiyesi", f"Bankanda sadece {format_money(account['bank'])} var.", 0xE74C3C),
                ephemeral=True
            )
            return

        embed = make_embed("Para cekildi", f"Cuzdanina {format_money(amount)} cektin.", 0x2ECC71)
        embed.add_field(name="Cuzdan", value=format_money(account["wallet"]), inline=True)
        embed.add_field(name="Banka", value=format_money(account["bank"]), inline=True)
        await interaction.response.send_message(embed=embed)
