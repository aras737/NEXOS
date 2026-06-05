from discord import app_commands

from core.economy import format_money, get_leaderboard
from core.embeds import make_embed


def register(bot):
    @bot.tree.command(name="leaderboard", description="Ekonomi liderlik tablosunu gosterir.")
    @app_commands.guild_only()
    async def leaderboard(interaction):
        rows = get_leaderboard(interaction.guild.id)

        if not rows:
            await interaction.response.send_message(
                embed=make_embed("Ekonomi liderleri", "Henuz ekonomi verisi yok.", 0xF1C40F),
                ephemeral=True
            )
            return

        lines = []
        for index, row in enumerate(rows, start=1):
            member = interaction.guild.get_member(row["user_id"])
            name = member.mention if member else f"`{row['user_id']}`"
            lines.append(f"**#{index}** {name} - {format_money(row['total'])}")

        embed = make_embed("Ekonomi liderleri", "\n".join(lines), 0xF1C40F)
        embed.set_footer(text="Siralama toplam cuzdan + banka bakiyesine gore hesaplanir.")
        await interaction.response.send_message(embed=embed)
