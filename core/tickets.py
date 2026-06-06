import asyncio

import discord

from core.embeds import make_embed
from core.logging import log_event
from core.storage import (
    add_ticket_user,
    close_ticket_record,
    create_ticket_record,
    find_open_ticket_for_user,
    get_guild_setting,
    get_ticket_record,
    remove_ticket_user,
    transcript_path,
    update_ticket_record
)


PANEL_COLOR = 0x8B5CF6

PRIORITY_COLORS = {
    "dusuk": 0x95A5A6,
    "normal": 0x5865F2,
    "yuksek": 0xE67E22,
    "acil": 0xE74C3C
}

PRIORITY_LABELS = {
    "dusuk": "Dusuk",
    "normal": "Normal",
    "yuksek": "Yuksek",
    "acil": "Acil"
}


def ticket_category_name():
    return "NEXOS TICKETS"


def safe_channel_name(user):
    base = user.name.lower()
    cleaned = "".join(char if char.isalnum() else "-" for char in base)
    cleaned = "-".join(part for part in cleaned.split("-") if part)
    suffix = user.discriminator if getattr(user, "discriminator", "0") != "0" else user.id % 10000
    return f"ticket-{cleaned[:20]}-{suffix}"


def clean_ticket_name(name):
    cleaned = "".join(char.lower() if char.isalnum() else "-" for char in str(name))
    cleaned = "-".join(part for part in cleaned.split("-") if part)
    if not cleaned:
        cleaned = "destek"
    return f"ticket-{cleaned[:80]}"


def normalize_priority(value):
    normalized = str(value or "normal").lower().strip()
    aliases = {
        "low": "dusuk",
        "düşük": "dusuk",
        "medium": "normal",
        "high": "yuksek",
        "yüksek": "yuksek",
        "urgent": "acil"
    }
    normalized = aliases.get(normalized, normalized)
    if normalized not in PRIORITY_COLORS:
        return "normal"
    return normalized


def parse_member_id(value):
    digits = "".join(char for char in str(value) if char.isdigit())
    return int(digits) if digits else None


def format_member(guild, user_id):
    member = guild.get_member(int(user_id)) if user_id else None
    return member.mention if member else str(user_id)


def is_ticket_staff(member):
    if member.guild_permissions.manage_channels:
        return True

    support_role_id = get_guild_setting(member.guild.id, "ticket_support_role_id")
    if not support_role_id:
        return False
    return any(role.id == int(support_role_id) for role in member.roles)


def is_ticket_owner(member, ticket):
    return member.id == int(ticket.get("owner_id", 0))


def can_use_ticket_controls(member, ticket):
    return is_ticket_owner(member, ticket) or is_ticket_staff(member)


async def get_or_create_ticket_category(guild):
    category_id = get_guild_setting(guild.id, "ticket_category_id")
    if category_id:
        category = guild.get_channel(int(category_id))
        if isinstance(category, discord.CategoryChannel):
            return category

    category = discord.utils.get(guild.categories, name=ticket_category_name())
    if category:
        return category

    return await guild.create_category(ticket_category_name(), reason="NEXOS ticket kategorisi")


def ticket_overwrites(guild, owner):
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        owner: discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            read_message_history=True,
            attach_files=True
        ),
        guild.me: discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            manage_channels=True,
            read_message_history=True
        )
    }

    support_role_id = get_guild_setting(guild.id, "ticket_support_role_id")
    if support_role_id:
        role = guild.get_role(int(support_role_id))
        if role:
            overwrites[role] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_channels=True
            )

    return overwrites


async def send_ephemeral(interaction, title, description, color=0xE74C3C):
    embed = make_embed(title, description, color)
    if interaction.response.is_done():
        await interaction.followup.send(embed=embed, ephemeral=True)
    else:
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def get_open_ticket_or_reply(interaction, staff_only=False, owner_or_staff=False):
    if not interaction.guild or not interaction.channel:
        await send_ephemeral(interaction, "Ticket Bulunamadi", "Bu islem sadece sunucu ticket kanalinda kullanilir.")
        return None

    ticket = get_ticket_record(interaction.guild.id, interaction.channel.id)
    if not ticket or ticket.get("status") != "open":
        await send_ephemeral(interaction, "Ticket Bulunamadi", "Bu kanal acik bir NEXOS ticket kanali degil.")
        return None

    if staff_only and not is_ticket_staff(interaction.user):
        await send_ephemeral(interaction, "Yetki Reddedildi", "Bu islem ticket yetkilileri icindir.")
        return None

    if owner_or_staff and not can_use_ticket_controls(interaction.user, ticket):
        await send_ephemeral(
            interaction,
            "Yetki Reddedildi",
            "Bu islemi sadece ticket sahibi veya ticket yetkilisi kullanabilir."
        )
        return None

    return ticket


async def fetch_member(guild, raw_value):
    member_id = parse_member_id(raw_value)
    if not member_id:
        return None

    member = guild.get_member(member_id)
    if member:
        return member

    try:
        return await guild.fetch_member(member_id)
    except (discord.NotFound, discord.HTTPException, discord.Forbidden):
        return None


def build_ticket_info_embed(guild, channel, ticket):
    priority = normalize_priority(ticket.get("priority", "normal"))
    claimed_by = ticket.get("claimed_by")
    added_users = ticket.get("added_users", [])
    added_text = ", ".join(format_member(guild, user_id) for user_id in added_users) if added_users else "Yok"

    embed = make_embed(
        "Ticket Bilgisi",
        ticket.get("subject", "Konu yok"),
        PRIORITY_COLORS.get(priority, 0x5865F2)
    )
    embed.add_field(name="Kanal", value=channel.mention, inline=True)
    embed.add_field(name="Sahip", value=format_member(guild, ticket.get("owner_id")), inline=True)
    embed.add_field(name="Durum", value=ticket.get("status", "bilinmiyor"), inline=True)
    embed.add_field(name="Oncelik", value=PRIORITY_LABELS.get(priority, priority), inline=True)
    embed.add_field(name="Ustlenen", value=format_member(guild, claimed_by) if claimed_by else "Yok", inline=True)
    embed.add_field(name="Eklenen Uyeler", value=added_text, inline=False)
    embed.add_field(name="Detay", value=ticket.get("details") or "Yok", inline=False)
    embed.set_footer(text=f"Olusturulma: {ticket.get('created_at', 'bilinmiyor')}")
    return embed


async def build_transcript(channel, limit=500):
    lines = []
    async for message in channel.history(limit=limit, oldest_first=True):
        created_at = message.created_at.isoformat()
        attachments = " ".join(attachment.url for attachment in message.attachments)
        content = message.content or ""
        if attachments:
            content = f"{content} {attachments}".strip()
        if message.embeds and not content:
            content = "[embed mesaj]"
        lines.append(f"[{created_at}] {message.author} ({message.author.id}): {content}")
    return "\n".join(lines) or "Transcript icin mesaj bulunamadi."


async def claim_ticket(interaction):
    ticket = await get_open_ticket_or_reply(interaction, staff_only=True)
    if not ticket:
        return

    update_ticket_record(interaction.guild.id, interaction.channel.id, claimed_by=interaction.user.id)
    await interaction.response.send_message(
        embed=make_embed("Ticket Ustlenildi", f"{interaction.user.mention} bu ticketi ustlendi.", 0x2ECC71)
    )
    await log_event(
        interaction.guild,
        "Ticket Claim",
        f"{interaction.channel} ticketi ustlenildi.",
        0x2ECC71,
        [("Yetkili", f"{interaction.user} ({interaction.user.id})")]
    )


async def show_ticket_info(interaction):
    ticket = await get_open_ticket_or_reply(interaction, owner_or_staff=True)
    if not ticket:
        return

    await interaction.response.send_message(
        embed=build_ticket_info_embed(interaction.guild, interaction.channel, ticket),
        ephemeral=True
    )


async def send_ticket_transcript(interaction, limit=500):
    ticket = await get_open_ticket_or_reply(interaction, owner_or_staff=True)
    if not ticket:
        return

    await interaction.response.defer(ephemeral=True, thinking=True)
    content = await build_transcript(interaction.channel, limit)
    path = transcript_path(interaction.guild.id, interaction.channel.id)
    path.write_text(content, encoding="utf-8")
    await interaction.followup.send(
        embed=make_embed("Transcript Hazir", f"Son {limit} mesaj icin transcript olusturuldu.", 0x2ECC71),
        file=discord.File(path),
        ephemeral=True
    )
    await log_event(
        interaction.guild,
        "Ticket Transcript",
        f"{interaction.channel} icin transcript olusturuldu.",
        0x3498DB,
        [
            ("Olusturan", f"{interaction.user} ({interaction.user.id})"),
            ("Limit", limit),
            ("Dosya", str(path))
        ]
    )


async def add_member_to_ticket(interaction, raw_member):
    ticket = await get_open_ticket_or_reply(interaction, staff_only=True)
    if not ticket:
        return

    member = await fetch_member(interaction.guild, raw_member)
    if not member:
        await send_ephemeral(interaction, "Uye Bulunamadi", "Gecerli bir uye ID'si veya etiket yazmalisin.")
        return

    await interaction.channel.set_permissions(
        member,
        view_channel=True,
        send_messages=True,
        read_message_history=True,
        attach_files=True
    )
    add_ticket_user(interaction.guild.id, interaction.channel.id, member.id)
    await interaction.response.send_message(
        embed=make_embed("Uye Eklendi", f"{member.mention} tickete eklendi.", 0x2ECC71)
    )
    await log_event(
        interaction.guild,
        "Ticket Uye Eklendi",
        f"{member} tickete eklendi.",
        0x2ECC71,
        [
            ("Yetkili", f"{interaction.user} ({interaction.user.id})"),
            ("Uye", f"{member} ({member.id})"),
            ("Kanal", f"{interaction.channel} ({interaction.channel_id})")
        ]
    )


async def remove_member_from_ticket(interaction, raw_member):
    ticket = await get_open_ticket_or_reply(interaction, staff_only=True)
    if not ticket:
        return

    member = await fetch_member(interaction.guild, raw_member)
    if not member:
        await send_ephemeral(interaction, "Uye Bulunamadi", "Gecerli bir uye ID'si veya etiket yazmalisin.")
        return

    if member.id == int(ticket["owner_id"]):
        await send_ephemeral(interaction, "Islem Reddedildi", "Ticket sahibini ticketten cikaramazsin.")
        return

    await interaction.channel.set_permissions(member, overwrite=None)
    remove_ticket_user(interaction.guild.id, interaction.channel.id, member.id)
    await interaction.response.send_message(
        embed=make_embed("Uye Cikarildi", f"{member.mention} ticketten cikarildi.", 0xE67E22)
    )
    await log_event(
        interaction.guild,
        "Ticket Uye Cikarildi",
        f"{member} ticketten cikarildi.",
        0xE67E22,
        [
            ("Yetkili", f"{interaction.user} ({interaction.user.id})"),
            ("Uye", f"{member} ({member.id})"),
            ("Kanal", f"{interaction.channel} ({interaction.channel_id})")
        ]
    )


async def rename_ticket(interaction, new_name):
    ticket = await get_open_ticket_or_reply(interaction, staff_only=True)
    if not ticket:
        return

    old_name = interaction.channel.name
    clean_name = clean_ticket_name(new_name)
    await interaction.channel.edit(name=clean_name, reason=f"NEXOS ticket rename: {interaction.user}")
    await interaction.response.send_message(
        embed=make_embed("Ticket Adi Degisti", f"`{old_name}` -> `{clean_name}`", 0x2ECC71)
    )
    await log_event(
        interaction.guild,
        "Ticket Rename",
        f"{old_name} ticket adi {clean_name} olarak degisti.",
        0x3498DB,
        [("Yetkili", f"{interaction.user} ({interaction.user.id})")]
    )


async def change_ticket_priority(interaction, priority):
    ticket = await get_open_ticket_or_reply(interaction, staff_only=True)
    if not ticket:
        return

    priority = normalize_priority(priority)
    update_ticket_record(interaction.guild.id, interaction.channel.id, priority=priority)
    await interaction.response.send_message(
        embed=make_embed(
            "Oncelik Guncellendi",
            f"Ticket onceligi: **{PRIORITY_LABELS[priority]}**",
            PRIORITY_COLORS[priority]
        )
    )
    await log_event(
        interaction.guild,
        "Ticket Oncelik",
        f"{interaction.channel} onceligi {PRIORITY_LABELS[priority]} yapildi.",
        PRIORITY_COLORS[priority],
        [("Yetkili", f"{interaction.user} ({interaction.user.id})")]
    )


async def close_ticket_channel(interaction, reason="Sebep belirtilmedi"):
    ticket = await get_open_ticket_or_reply(interaction, owner_or_staff=True)
    if not ticket:
        return

    close_ticket_record(interaction.guild.id, interaction.channel.id, reason)
    await interaction.response.send_message(
        embed=make_embed("Ticket Kapatiliyor", f"Ticket 3 saniye icinde kapatilacak.\nSebep: {reason}", 0xE67E22),
        ephemeral=True
    )
    await log_event(
        interaction.guild,
        "Ticket Kapatildi",
        f"{interaction.channel} ticketi kapatildi.",
        0xE67E22,
        [
            ("Kapatan", f"{interaction.user} ({interaction.user.id})"),
            ("Ticket Sahibi", str(ticket["owner_id"])),
            ("Sebep", reason)
        ]
    )
    await asyncio.sleep(3)

    try:
        await interaction.channel.delete(reason=f"NEXOS ticket kapatildi: {reason}")
    except discord.NotFound:
        pass


class TicketAddUserModal(discord.ui.Modal, title="Tickete Uye Ekle"):
    member = discord.ui.TextInput(
        label="Uye ID veya etiket",
        placeholder="123456789012345678 veya @uye",
        min_length=1,
        max_length=64
    )

    async def on_submit(self, interaction):
        await add_member_to_ticket(interaction, str(self.member))


class TicketRemoveUserModal(discord.ui.Modal, title="Ticketten Uye Cikar"):
    member = discord.ui.TextInput(
        label="Uye ID veya etiket",
        placeholder="123456789012345678 veya @uye",
        min_length=1,
        max_length=64
    )

    async def on_submit(self, interaction):
        await remove_member_from_ticket(interaction, str(self.member))


class TicketRenameModal(discord.ui.Modal, title="Ticket Adini Degistir"):
    name = discord.ui.TextInput(
        label="Yeni ticket adi",
        placeholder="ornek: destek-odeme",
        min_length=3,
        max_length=80
    )

    async def on_submit(self, interaction):
        await rename_ticket(interaction, str(self.name))


class TicketCloseModal(discord.ui.Modal, title="Ticket Kapat"):
    reason = discord.ui.TextInput(
        label="Kapatma sebebi",
        placeholder="Sorun cozuldu",
        default="Sebep belirtilmedi",
        min_length=1,
        max_length=180,
        required=False
    )

    async def on_submit(self, interaction):
        await close_ticket_channel(interaction, str(self.reason) or "Sebep belirtilmedi")


class TicketControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Ustlen", style=discord.ButtonStyle.success, custom_id="nexos:ticket_claim", row=0)
    async def claim_button(self, interaction, _button):
        await claim_ticket(interaction)

    @discord.ui.button(label="Bilgi", style=discord.ButtonStyle.secondary, custom_id="nexos:ticket_info", row=0)
    async def info_button(self, interaction, _button):
        await show_ticket_info(interaction)

    @discord.ui.button(label="Transcript", style=discord.ButtonStyle.secondary, custom_id="nexos:ticket_transcript", row=0)
    async def transcript_button(self, interaction, _button):
        await send_ticket_transcript(interaction)

    @discord.ui.button(label="Uye Ekle", style=discord.ButtonStyle.primary, custom_id="nexos:ticket_add_user", row=1)
    async def add_user_button(self, interaction, _button):
        ticket = await get_open_ticket_or_reply(interaction, staff_only=True)
        if ticket:
            await interaction.response.send_modal(TicketAddUserModal())

    @discord.ui.button(label="Uye Cikar", style=discord.ButtonStyle.secondary, custom_id="nexos:ticket_remove_user", row=1)
    async def remove_user_button(self, interaction, _button):
        ticket = await get_open_ticket_or_reply(interaction, staff_only=True)
        if ticket:
            await interaction.response.send_modal(TicketRemoveUserModal())

    @discord.ui.button(label="Yeniden Adlandir", style=discord.ButtonStyle.secondary, custom_id="nexos:ticket_rename", row=1)
    async def rename_button(self, interaction, _button):
        ticket = await get_open_ticket_or_reply(interaction, staff_only=True)
        if ticket:
            await interaction.response.send_modal(TicketRenameModal())

    @discord.ui.button(label="Ticket Kapat", style=discord.ButtonStyle.danger, custom_id="nexos:ticket_close", row=1)
    async def close_button(self, interaction, _button):
        ticket = await get_open_ticket_or_reply(interaction, owner_or_staff=True)
        if ticket:
            await interaction.response.send_modal(TicketCloseModal())

    @discord.ui.select(
        placeholder="Oncelik degistir",
        custom_id="nexos:ticket_priority",
        row=2,
        options=[
            discord.SelectOption(label="Dusuk", value="dusuk", description="Acil olmayan destek"),
            discord.SelectOption(label="Normal", value="normal", description="Standart destek"),
            discord.SelectOption(label="Yuksek", value="yuksek", description="Hizli bakilmasi gereken destek"),
            discord.SelectOption(label="Acil", value="acil", description="Kritik durum")
        ]
    )
    async def priority_select(self, interaction, select):
        await change_ticket_priority(interaction, select.values[0])


class TicketModal(discord.ui.Modal, title="NEXOS Ticket"):
    subject = discord.ui.TextInput(
        label="Konu",
        placeholder="Sorunu kisaca yaz",
        min_length=3,
        max_length=120
    )
    priority = discord.ui.TextInput(
        label="Oncelik",
        placeholder="dusuk / normal / yuksek / acil",
        default="normal",
        min_length=3,
        max_length=10,
        required=False
    )
    details = discord.ui.TextInput(
        label="Detay",
        placeholder="Yetkilinin bilmesi gereken detaylari yaz",
        min_length=0,
        max_length=800,
        required=False,
        style=discord.TextStyle.paragraph
    )

    async def on_submit(self, interaction):
        await create_ticket(interaction, str(self.subject), str(self.details), str(self.priority))


class TicketPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Ticket Ac", style=discord.ButtonStyle.primary, custom_id="nexos:ticket_open")
    async def open_button(self, interaction, _button):
        await interaction.response.send_modal(TicketModal())


async def create_ticket(interaction, subject, details="", priority="normal"):
    priority = normalize_priority(priority)
    existing_channel_id, _ticket = find_open_ticket_for_user(interaction.guild.id, interaction.user.id)
    if existing_channel_id:
        channel = interaction.guild.get_channel(existing_channel_id)
        if channel:
            await interaction.response.send_message(
                embed=make_embed("Ticket Zaten Acik", f"Zaten acik ticket kanaliniz var: {channel.mention}", 0xE67E22),
                ephemeral=True
            )
            return

    category = await get_or_create_ticket_category(interaction.guild)
    channel = await interaction.guild.create_text_channel(
        safe_channel_name(interaction.user),
        category=category,
        overwrites=ticket_overwrites(interaction.guild, interaction.user),
        reason=f"NEXOS ticket: {interaction.user}"
    )

    create_ticket_record(interaction.guild.id, channel.id, interaction.user.id, subject, details, priority)

    support_role_id = get_guild_setting(interaction.guild.id, "ticket_support_role_id")
    support_role = interaction.guild.get_role(int(support_role_id)) if support_role_id else None
    content = interaction.user.mention
    if support_role:
        content = f"{interaction.user.mention} {support_role.mention}"

    embed = make_embed(
        "Ticket Acildi",
        f"{interaction.user.mention} destek talebi olusturdu.",
        PRIORITY_COLORS[priority]
    )
    embed.add_field(name="Konu", value=subject, inline=False)
    embed.add_field(name="Oncelik", value=PRIORITY_LABELS[priority], inline=True)
    embed.add_field(name="Aciklama", value=details or "Yok", inline=False)
    embed.add_field(
        name="Kontroller",
        value="Bu ticket icin ustlenme, oncelik, uye ekleme/cikarma, isim, bilgi, transcript ve kapatma islemleri asagidaki panelden yapilir.",
        inline=False
    )
    embed.set_footer(text="Ticketler sadece ana panelden acilir; bu kanal icinde her sey butonlarla yonetilir.")
    await channel.send(content=content, embed=embed, view=TicketControlView())
    await interaction.response.send_message(
        embed=make_embed("Ticket Acildi", f"Ticket kanaliniz: {channel.mention}", 0x2ECC71),
        ephemeral=True
    )
    await log_event(
        interaction.guild,
        "Ticket Acildi",
        f"{interaction.user} ticket acti.",
        0x2ECC71,
        [
            ("Kanal", f"{channel} ({channel.id})"),
            ("Konu", subject),
            ("Oncelik", PRIORITY_LABELS[priority]),
            ("Aciklama", details or "Yok")
        ]
    )
