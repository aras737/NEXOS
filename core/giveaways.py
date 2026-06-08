import asyncio
import datetime
import random
import re

import discord

from core.embeds import make_embed
from core.emojis import emoji, with_emoji
from core.logging import log_event
from core.storage import (
    add_giveaway_participant,
    close_giveaway_record,
    create_giveaway_record,
    get_giveaway_record,
    list_giveaway_records,
    update_giveaway_record
)


GIVEAWAY_COLOR = 0xF1C40F
GIVEAWAY_END_COLOR = 0x8B5CF6
MIN_DURATION_SECONDS = 60
MAX_DURATION_SECONDS = 60 * 60 * 24 * 90
DURATION_PATTERN = re.compile(r"(\d+)\s*([smhdw])", re.IGNORECASE)


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc)


def parse_duration(value):
    text = str(value or "").strip().lower()
    units = {
        "s": 1,
        "m": 60,
        "h": 60 * 60,
        "d": 60 * 60 * 24,
        "w": 60 * 60 * 24 * 7
    }
    total = 0
    consumed = ""
    for amount, unit in DURATION_PATTERN.findall(text):
        total += int(amount) * units[unit.lower()]
        consumed += f"{amount}{unit}"

    compact = re.sub(r"\s+", "", text)
    if not total or consumed.lower() != compact:
        return None
    if total < MIN_DURATION_SECONDS or total > MAX_DURATION_SECONDS:
        return None
    return total


def iso_from_seconds(seconds):
    return (utc_now() + datetime.timedelta(seconds=seconds)).isoformat()


def parse_iso(value):
    return datetime.datetime.fromisoformat(value)


def unix_timestamp(iso_value):
    return int(parse_iso(iso_value).timestamp())


def mention_list(user_ids):
    return ", ".join(f"<@{user_id}>" for user_id in user_ids) if user_ids else "Yok"


def participant_count(record):
    return len(record.get("participants", []))


def giveaway_embed(record):
    status = record.get("status", "open")
    ends_at = record.get("ends_at")
    winners = record.get("winner_ids", [])
    required_role_id = record.get("required_role_id")
    is_open = status == "open"
    title = with_emoji("giveaway", "Cekilis Basladi") if is_open else with_emoji("gift", "Cekilis Bitti")
    description = record.get("description") or "Katilmak icin butona bas."

    embed = make_embed(title, description, GIVEAWAY_COLOR if is_open else GIVEAWAY_END_COLOR)
    embed.add_field(name="Odul", value=record.get("prize", "Bilinmiyor"), inline=False)
    embed.add_field(name="Kazanan Sayisi", value=str(record.get("winners_count", 1)), inline=True)
    embed.add_field(name="Katilimci", value=str(participant_count(record)), inline=True)
    embed.add_field(name="Duzenleyen", value=f"<@{record.get('host_id')}>", inline=True)
    if ends_at:
        timestamp = unix_timestamp(ends_at)
        embed.add_field(name="Bitis", value=f"<t:{timestamp}:F>\n<t:{timestamp}:R>", inline=False)
    if required_role_id:
        embed.add_field(name="Gerekli Rol", value=f"<@&{required_role_id}>", inline=True)
    if winners:
        embed.add_field(name="Kazananlar", value=mention_list(winners), inline=False)
    if not is_open:
        embed.add_field(name="Durum", value=record.get("end_reason") or "Bitti", inline=True)
    embed.set_footer(text=f"NEXOS Cekilis ID: {record.get('message_id')}")
    return embed


async def fetch_giveaway_message(bot, record):
    channel = bot.get_channel(int(record["channel_id"]))
    if not channel:
        try:
            channel = await bot.fetch_channel(int(record["channel_id"]))
        except (discord.HTTPException, discord.NotFound, discord.Forbidden):
            return None

    try:
        return await channel.fetch_message(int(record["message_id"]))
    except (discord.HTTPException, discord.NotFound, discord.Forbidden):
        return None


async def eligible_participants(guild, record, exclude=None):
    exclude = set(int(item) for item in (exclude or []))
    required_role_id = record.get("required_role_id")
    eligible = []

    for user_id in record.get("participants", []):
        user_id = int(user_id)
        if user_id in exclude:
            continue

        member = guild.get_member(user_id)
        if not member:
            try:
                member = await guild.fetch_member(user_id)
            except (discord.NotFound, discord.HTTPException, discord.Forbidden):
                continue
        if member.bot:
            continue
        if required_role_id and not any(role.id == int(required_role_id) for role in member.roles):
            continue
        eligible.append(user_id)

    return eligible


async def pick_winners(guild, record, exclude=None):
    eligible = await eligible_participants(guild, record, exclude=exclude)
    if not eligible:
        return []

    count = min(int(record.get("winners_count", 1)), len(eligible))
    return random.SystemRandom().sample(eligible, count)


async def refresh_giveaway_message(bot, record):
    message = await fetch_giveaway_message(bot, record)
    if not message:
        return False
    view = GiveawayView() if record.get("status") == "open" else None
    await message.edit(embed=giveaway_embed(record), view=view)
    return True


async def create_giveaway(interaction, channel, prize, duration, winners_count, description="", required_role=None):
    seconds = parse_duration(duration)
    if not seconds:
        await interaction.response.send_message(
            embed=make_embed("Sure Gecersiz", "Sure ornegi: `10m`, `1h`, `2d`, `1w`. En az 1 dakika, en fazla 90 gun.", 0xE74C3C),
            ephemeral=True
        )
        return None

    if winners_count < 1 or winners_count > 20:
        await interaction.response.send_message(
            embed=make_embed("Kazanan Sayisi Gecersiz", "Kazanan sayisi 1 ile 20 arasinda olmali.", 0xE74C3C),
            ephemeral=True
        )
        return None

    ends_at = iso_from_seconds(seconds)
    placeholder = {
        "guild_id": interaction.guild.id,
        "channel_id": channel.id,
        "message_id": 0,
        "host_id": interaction.user.id,
        "prize": prize,
        "description": description or "Katilmak icin butona bas.",
        "winners_count": winners_count,
        "ends_at": ends_at,
        "required_role_id": required_role.id if required_role else None,
        "participants": [],
        "winner_ids": [],
        "status": "open"
    }
    message = await channel.send(embed=giveaway_embed(placeholder), view=GiveawayView())
    record = create_giveaway_record(
        interaction.guild.id,
        channel.id,
        message.id,
        interaction.user.id,
        prize,
        description or "Katilmak icin butona bas.",
        winners_count,
        ends_at,
        required_role.id if required_role else None
    )
    await message.edit(embed=giveaway_embed(record), view=GiveawayView())
    await interaction.response.send_message(
        embed=make_embed("Cekilis Baslatildi", f"Cekilis {channel.mention} kanalinda baslatildi.\nID: `{message.id}`", 0x2ECC71),
        ephemeral=True
    )
    await log_event(
        interaction.guild,
        "Cekilis Baslatildi",
        f"{prize} cekilisi baslatildi.",
        GIVEAWAY_COLOR,
        [
            ("Yetkili", f"{interaction.user} ({interaction.user.id})"),
            ("Kanal", f"{channel} ({channel.id})"),
            ("Cekilis ID", message.id),
            ("Odul", prize),
            ("Bitis", ends_at),
            ("Kazanan Sayisi", winners_count)
        ],
        log_type="mod"
    )
    return record


async def finish_giveaway(bot, guild, record, reason="Sure bitti", forced_by=None):
    if not record or record.get("status") != "open":
        return record

    winners = await pick_winners(guild, record)
    record = close_giveaway_record(guild.id, record["message_id"], winners, reason)
    await refresh_giveaway_message(bot, record)

    message = await fetch_giveaway_message(bot, record)
    channel = message.channel if message else bot.get_channel(int(record["channel_id"]))
    if channel:
        if winners:
            await channel.send(
                f"{emoji('giveaway')} Tebrikler {mention_list(winners)}! "
                f"**{record['prize']}** cekilisini kazandiniz."
            )
        else:
            await channel.send(f"{emoji('warn')} **{record['prize']}** cekilisinde yeterli katilim olmadigi icin kazanan yok.")

    await log_event(
        guild,
        "Cekilis Bitti",
        f"{record['prize']} cekilisi bitti.",
        GIVEAWAY_END_COLOR,
        [
            ("Cekilis ID", record["message_id"]),
            ("Odul", record["prize"]),
            ("Kazananlar", mention_list(winners)),
            ("Katilimci", participant_count(record)),
            ("Sebep", reason),
            ("Bitiren", forced_by or "Otomatik")
        ],
        log_type="mod"
    )
    return record


async def reroll_giveaway(bot, guild, record, actor):
    if not record or record.get("status") != "ended":
        return None

    winners = await pick_winners(guild, record, exclude=record.get("winner_ids", []))
    if not winners:
        winners = await pick_winners(guild, record)
    if not winners:
        return []

    record = update_giveaway_record(guild.id, record["message_id"], winner_ids=winners, end_reason="reroll")
    await refresh_giveaway_message(bot, record)
    channel = bot.get_channel(int(record["channel_id"]))
    if channel:
        await channel.send(f"{emoji('gift')} Yeni cekilis kazananlari: {mention_list(winners)} | Odul: **{record['prize']}**")

    await log_event(
        guild,
        "Cekilis Reroll",
        f"{record['prize']} cekilisi icin yeni kazanan secildi.",
        GIVEAWAY_END_COLOR,
        [
            ("Yetkili", f"{actor} ({actor.id})"),
            ("Cekilis ID", record["message_id"]),
            ("Yeni Kazananlar", mention_list(winners))
        ],
        log_type="mod"
    )
    return winners


async def cancel_giveaway(bot, guild, record, actor):
    if not record or record.get("status") != "open":
        return None

    record = close_giveaway_record(guild.id, record["message_id"], [], "Iptal edildi")
    await refresh_giveaway_message(bot, record)
    await log_event(
        guild,
        "Cekilis Iptal",
        f"{record['prize']} cekilisi iptal edildi.",
        0xE74C3C,
        [
            ("Yetkili", f"{actor} ({actor.id})"),
            ("Cekilis ID", record["message_id"]),
            ("Odul", record["prize"])
        ],
        log_type="mod"
    )
    return record


async def process_due_giveaways(bot):
    for guild in bot.guilds:
        for record in list_giveaway_records(guild.id, status="open"):
            try:
                if parse_iso(record["ends_at"]) <= utc_now():
                    await finish_giveaway(bot, guild, record)
            except Exception as error:
                await log_event(
                    guild,
                    "Cekilis Hata",
                    "Cekilis otomatik bitirilirken hata olustu.",
                    0xE74C3C,
                    [
                        ("Cekilis ID", record.get("message_id")),
                        ("Hata", f"{type(error).__name__}: {error}")
                    ],
                    log_type="mod"
                )


async def giveaway_watcher(bot):
    await bot.wait_until_ready()
    while not bot.is_closed():
        await process_due_giveaways(bot)
        await asyncio.sleep(30)


class GiveawayView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Cekilise Katil", style=discord.ButtonStyle.success, custom_id="nexos:giveaway_join")
    async def join_button(self, interaction, _button):
        if not interaction.guild or not interaction.message:
            await interaction.response.send_message("Bu buton sadece sunucuda kullanilir.", ephemeral=True)
            return

        record = get_giveaway_record(interaction.guild.id, interaction.message.id)
        if not record:
            await interaction.response.send_message(
                embed=make_embed("Cekilis Bulunamadi", "Bu cekilis datasi bulunamadi.", 0xE74C3C),
                ephemeral=True
            )
            return
        if record.get("status") != "open":
            await interaction.response.send_message(
                embed=make_embed("Cekilis Bitti", "Bu cekilis artik aktif degil.", 0xE67E22),
                ephemeral=True
            )
            return
        if interaction.user.bot:
            await interaction.response.send_message(
                embed=make_embed("Katilim Reddedildi", "Botlar cekilise katilamaz.", 0xE74C3C),
                ephemeral=True
            )
            return

        required_role_id = record.get("required_role_id")
        if required_role_id and not any(role.id == int(required_role_id) for role in interaction.user.roles):
            await interaction.response.send_message(
                embed=make_embed("Rol Gerekli", f"Bu cekilise katilmak icin <@&{required_role_id}> rolu gerekli.", 0xE74C3C),
                ephemeral=True
            )
            return

        if interaction.user.id in [int(item) for item in record.get("participants", [])]:
            await interaction.response.send_message(
                embed=make_embed("Zaten Katildin", "Bu cekilise zaten katildin.", 0xE67E22),
                ephemeral=True
            )
            return

        record = add_giveaway_participant(interaction.guild.id, interaction.message.id, interaction.user.id)
        await interaction.message.edit(embed=giveaway_embed(record), view=GiveawayView())
        await interaction.response.send_message(
            embed=make_embed("Cekilise Katildin", f"Bol sans! Odul: **{record['prize']}**", 0x2ECC71),
            ephemeral=True
        )
        await log_event(
            interaction.guild,
            "Cekilis Katilim",
            f"{interaction.user} cekilise katildi.",
            GIVEAWAY_COLOR,
            [
                ("Uye", f"{interaction.user} ({interaction.user.id})"),
                ("Cekilis ID", record["message_id"]),
                ("Odul", record["prize"]),
                ("Toplam Katilimci", participant_count(record))
            ],
            log_type="mod"
        )
