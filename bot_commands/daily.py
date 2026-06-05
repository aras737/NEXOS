from discord import app_commands

from core.economy import claim_daily, format_money, remaining_text
from core.embeds import make_embed


def register(bot):
    @bot.tree.command(name="daily", description="Gunluk ekonomi odulunu alir.")
    @app_commands.guild_only()
    @app_commands.default_permissions(send_messages=True)
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def daily(interaction):
        claimed, result, account = claim_daily(interaction.guild.id, interaction.user.id)

        if not claimed:
            await interaction.response.send_message(
                embed=make_embed("Gunluk odul beklemede", f"Tekrar almak icin kalan sure: {remaining_text(result)}", 0xE67E22),
                ephemeral=True
            )
            return

        embed = make_embed("Gunluk odul alindi", f"Hesabina {format_money(result)} eklendi.", 0x2ECC71)
        embed.add_field(name="Cuzdan", value=format_money(account["wallet"]), inline=True)
        embed.add_field(name="Banka", value=format_money(account["bank"]), inline=True)
        embed.set_footer(text="24 saatte bir kullanilabilir.")
        await interaction.response.send_message(embed=embed)
