from discord import app_commands

from core.economy import format_money, remaining_text
from core.economy import work as work_job
from core.embeds import make_embed


def register(bot):
    @bot.tree.command(name="work", description="Calisip ekonomi kredisi kazanir.")
    @app_commands.guild_only()
    async def work(interaction):
        success, result, account, job = work_job(interaction.guild.id, interaction.user.id)

        if not success:
            await interaction.response.send_message(
                embed=make_embed("Calisma beklemede", f"Tekrar calismak icin kalan sure: {remaining_text(result)}", 0xE67E22),
                ephemeral=True
            )
            return

        embed = make_embed("Calisma tamamlandi", f"{job} ve {format_money(result)} kazandin.", 0x2ECC71)
        embed.add_field(name="Cuzdan", value=format_money(account["wallet"]), inline=True)
        embed.add_field(name="Banka", value=format_money(account["bank"]), inline=True)
        embed.set_footer(text="30 dakikada bir kullanilabilir.")
        await interaction.response.send_message(embed=embed)
