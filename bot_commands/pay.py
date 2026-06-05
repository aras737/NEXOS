import discord
from discord import app_commands

from core.economy import format_money, transfer
from core.embeds import make_embed


def register(bot):
    @bot.tree.command(name="pay", description="Baska bir uyeye cuzdanindan para gonderir.")
    @app_commands.guild_only()
    @app_commands.default_permissions(send_messages=True)
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def pay(interaction, member: discord.Member, amount: app_commands.Range[int, 1, 1000000000]):
        if member.bot:
            await interaction.response.send_message(
                embed=make_embed("Gonderim reddedildi", "Botlara para gonderemezsin.", 0xE74C3C),
                ephemeral=True
            )
            return

        if member.id == interaction.user.id:
            await interaction.response.send_message(
                embed=make_embed("Gonderim reddedildi", "Kendine para gonderemezsin.", 0xE74C3C),
                ephemeral=True
            )
            return

        success, sender, _receiver = transfer(interaction.guild.id, interaction.user.id, member.id, amount)
        if not success:
            await interaction.response.send_message(
                embed=make_embed("Yetersiz bakiye", f"Cuzdaninda sadece {format_money(sender['wallet'])} var.", 0xE74C3C),
                ephemeral=True
            )
            return

        embed = make_embed("Para gonderildi", f"{member.mention} uyesine {format_money(amount)} gonderdin.", 0x2ECC71)
        embed.add_field(name="Kalan cuzdan", value=format_money(sender["wallet"]), inline=True)
        await interaction.response.send_message(embed=embed)
