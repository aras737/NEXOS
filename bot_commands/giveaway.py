import datetime

import discord
from discord import app_commands

from core.embeds import make_embed
from core.giveaways import (
    cancel_giveaway,
    create_giveaway,
    finish_giveaway,
    parse_duration,
    reroll_giveaway
)
from core.storage import get_giveaway_record, list_giveaway_records


def parse_message_id(value):
    digits = "".join(char for char in str(value) if char.isdigit())
    return int(digits) if digits else None


def giveaway_line(record):
    return (
        f"`{record['message_id']}` | **{record['prize']}** | "
        f"<#{record['channel_id']}> | <t:{int(datetime.datetime.fromisoformat(record['ends_at']).timestamp())}:R> | "
        f"{len(record.get('participants', []))} katilimci"
    )


def find_giveaway_or_reply(interaction, message_id):
    giveaway_id = parse_message_id(message_id)
    if not giveaway_id:
        return None, make_embed("Cekilis ID Gecersiz", "Cekilis mesaj ID'si girmelisin.", 0xE74C3C)

    record = get_giveaway_record(interaction.guild.id, giveaway_id)
    if not record:
        return None, make_embed("Cekilis Bulunamadi", "Bu ID ile kayitli cekilis bulunamadi.", 0xE74C3C)
    return record, None


def register(bot):
    @bot.tree.command(name="giveaway-start", description="Butonlu cekilis baslatir.")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.bot_has_permissions(send_messages=True, embed_links=True, read_message_history=True)
    @app_commands.describe(
        prize="Cekilis odulu.",
        duration="Sure: 10m, 1h, 2d, 1w gibi.",
        winners="Kazanan sayisi.",
        channel="Cekilisin gonderilecegi kanal. Bos birakilirsa mevcut kanal.",
        description="Cekilis aciklamasi.",
        required_role="Katilim icin gerekli rol."
    )
    async def giveaway_start(
        interaction,
        prize: app_commands.Range[str, 1, 200],
        duration: app_commands.Range[str, 2, 16],
        winners: app_commands.Range[int, 1, 20] = 1,
        channel: discord.TextChannel | None = None,
        description: app_commands.Range[str, 1, 800] | None = None,
        required_role: discord.Role | None = None
    ):
        if not parse_duration(duration):
            await interaction.response.send_message(
                embed=make_embed("Sure Gecersiz", "Sure ornegi: `10m`, `1h`, `2d`, `1w`. En az 1 dakika, en fazla 90 gun.", 0xE74C3C),
                ephemeral=True
            )
            return
        await create_giveaway(
            interaction,
            channel or interaction.channel,
            str(prize),
            str(duration),
            int(winners),
            str(description) if description else "",
            required_role
        )

    @bot.tree.command(name="giveaway-end", description="Aktif cekilisi hemen bitirir.")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.bot_has_permissions(send_messages=True, embed_links=True, read_message_history=True)
    async def giveaway_end(interaction, message_id: str):
        record, error = find_giveaway_or_reply(interaction, message_id)
        if error:
            await interaction.response.send_message(embed=error, ephemeral=True)
            return
        if record.get("status") != "open":
            await interaction.response.send_message(
                embed=make_embed("Cekilis Aktif Degil", "Bu cekilis zaten bitmis veya iptal edilmis.", 0xE67E22),
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)
        await finish_giveaway(
            interaction.client,
            interaction.guild,
            record,
            reason="Yetkili tarafindan bitirildi",
            forced_by=f"{interaction.user} ({interaction.user.id})"
        )
        await interaction.followup.send(embed=make_embed("Cekilis Bitirildi", f"Cekilis `{record['message_id']}` bitirildi.", 0x2ECC71), ephemeral=True)

    @bot.tree.command(name="giveaway-reroll", description="Bitmis cekilis icin yeni kazanan secer.")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.bot_has_permissions(send_messages=True, embed_links=True, read_message_history=True)
    async def giveaway_reroll(interaction, message_id: str):
        record, error = find_giveaway_or_reply(interaction, message_id)
        if error:
            await interaction.response.send_message(embed=error, ephemeral=True)
            return
        if record.get("status") != "ended":
            await interaction.response.send_message(
                embed=make_embed("Cekilis Bitmemis", "Reroll icin cekilis bitmis olmali.", 0xE74C3C),
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)
        winners = await reroll_giveaway(interaction.client, interaction.guild, record, interaction.user)
        if winners is None:
            await interaction.followup.send(embed=make_embed("Cekilis Bulunamadi", "Cekilis kaydi bulunamadi.", 0xE74C3C), ephemeral=True)
            return
        if not winners:
            await interaction.followup.send(embed=make_embed("Kazanan Yok", "Reroll icin uygun katilimci yok.", 0xE67E22), ephemeral=True)
            return
        await interaction.followup.send(embed=make_embed("Yeni Kazanan Secildi", ", ".join(f"<@{item}>" for item in winners), 0x2ECC71), ephemeral=True)

    @bot.tree.command(name="giveaway-cancel", description="Aktif cekilisi iptal eder.")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.bot_has_permissions(send_messages=True, embed_links=True, read_message_history=True)
    async def giveaway_cancel(interaction, message_id: str):
        record, error = find_giveaway_or_reply(interaction, message_id)
        if error:
            await interaction.response.send_message(embed=error, ephemeral=True)
            return
        if record.get("status") != "open":
            await interaction.response.send_message(
                embed=make_embed("Cekilis Aktif Degil", "Sadece aktif cekilis iptal edilebilir.", 0xE74C3C),
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)
        await cancel_giveaway(interaction.client, interaction.guild, record, interaction.user)
        await interaction.followup.send(embed=make_embed("Cekilis Iptal Edildi", f"Cekilis `{record['message_id']}` iptal edildi.", 0x2ECC71), ephemeral=True)

    @bot.tree.command(name="giveaway-list", description="Aktif cekilisleri listeler.")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def giveaway_list(interaction):
        records = list_giveaway_records(interaction.guild.id, status="open")
        if not records:
            await interaction.response.send_message(
                embed=make_embed("Aktif Cekilis Yok", "Bu sunucuda aktif cekilis bulunmuyor.", 0xE67E22),
                ephemeral=True
            )
            return

        lines = [giveaway_line(record) for record in records[:10]]
        embed = make_embed("Aktif Cekilisler", "\n".join(lines), 0xF1C40F)
        if len(records) > 10:
            embed.set_footer(text=f"Toplam {len(records)} aktif cekilis var, ilk 10 gosteriliyor.")
        await interaction.response.send_message(embed=embed, ephemeral=True)
