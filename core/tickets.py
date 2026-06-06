import discord

from core.embeds import make_embed
from core.logging import log_event
from core.storage import create_ticket_record, find_open_ticket_for_user, get_guild_setting


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
    return f"ticket-{cleaned[:20]}-{user.discriminator if getattr(user, 'discriminator', '0') != '0' else user.id % 10000}"


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


def is_ticket_staff(member):
    if member.guild_permissions.manage_channels:
        return True

    support_role_id = get_guild_setting(member.guild.id, "ticket_support_role_id")
    if not support_role_id:
        return False
    return any(role.id == int(support_role_id) for role in member.roles)


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


class TicketCloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Ticket Kapat", style=discord.ButtonStyle.danger, custom_id="nexos:ticket_close")
    async def close_button(self, interaction, _button):
        from bot_commands.ticket_close import close_ticket_channel

        await close_ticket_channel(interaction, reason="Buton ile kapatildi")


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
    embed = make_embed(
        "Ticket Acildi",
        f"{interaction.user.mention} ticket acti.",
        PRIORITY_COLORS[priority]
    )
    embed.add_field(name="Konu", value=subject, inline=False)
    embed.add_field(name="Oncelik", value=PRIORITY_LABELS[priority], inline=True)
    embed.add_field(name="Aciklama", value=details or "Yok", inline=False)
    embed.set_footer(text="Is bitince butondan ticketi kapatabilirsin.")
    await channel.send(content=interaction.user.mention, embed=embed, view=TicketCloseView())
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
