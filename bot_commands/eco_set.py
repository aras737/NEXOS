import discord
from discord import app_commands

from core.economy import format_money, set_money
from core.embeds import make_embed
from core.logging import log_event


def register(bot):
    @bot.tree.command(name="eco-set", description="Yetkili olarak uye ekonomi bakiyesini ayarlar.")
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def eco_set(
        interaction,
        member: discord.Member,
        wallet: int | None = None,
        bank: int | None = None,
        reason: str = "Sebep belirtilmedi"
    ):
        if wallet is None and bank is None:
            await interaction.response.send_message(
                embed=make_embed("Eksik Deger", "Cuzdan veya banka degerlerinden en az birini girmelisin.", 0xE74C3C),
                ephemeral=True
            )
            return
        if wallet is not None and wallet < 0:
            await interaction.response.send_message(
                embed=make_embed("Gecersiz Deger", "Cuzdan degeri negatif olamaz.", 0xE74C3C),
                ephemeral=True
            )
            return
        if bank is not None and bank < 0:
            await interaction.response.send_message(
                embed=make_embed("Gecersiz Deger", "Banka degeri negatif olamaz.", 0xE74C3C),
                ephemeral=True
            )
            return

        account = set_money(interaction.guild.id, member.id, wallet=wallet, bank=bank)
        embed = make_embed("Ekonomi Ayarlandi", f"{member.mention} bakiyesi guncellendi.", 0x2ECC71)
        embed.add_field(name="Cuzdan", value=format_money(account["wallet"]), inline=True)
        embed.add_field(name="Banka", value=format_money(account["bank"]), inline=True)
        embed.add_field(name="Sebep", value=reason, inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await log_event(
            interaction.guild,
            "Eco Set",
            f"{member} bakiyesi ayarlandi.",
            0x2ECC71,
            [
                ("Yetkili", f"{interaction.user} ({interaction.user.id})"),
                ("Uye", f"{member} ({member.id})"),
                ("Cuzdan", format_money(account["wallet"])),
                ("Banka", format_money(account["bank"])),
                ("Sebep", reason)
            ]
        )
