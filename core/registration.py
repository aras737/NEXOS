import re

import discord

from core.embeds import make_embed
from core.emojis import with_emoji
from core.logging import log_event, normalize_text, trim
from core.permissions import role_hierarchy_error, self_assign_role_permission_error
from core.storage import get_guild_setting, upsert_registration_record


REGISTER_FORMAT = re.compile(r"^\s*(?P<name>[^|\n]{2,32})\s*\|\s*(?P<age>\d{1,2})\s*$")
MIN_AGE = 7
MAX_AGE = 99
DEFAULT_REGISTER_ALIASES = {"kayit", "kayit-kanali", "register", "registration"}
DEFAULT_MEMBER_ROLE_NAMES = {"uye", "kayitli", "member", "registered"}


class RegistrationError(Exception):
    pass


def clean_name(value):
    name = " ".join(str(value or "").replace("@", "").split())
    if len(name) < 2:
        raise RegistrationError("Isim en az 2 karakter olmali.")
    return name[:32]


def parse_registration_content(content):
    match = REGISTER_FORMAT.match(content or "")
    if not match:
        raise RegistrationError("Format `Isim | Yas` seklinde olmali.")

    name = clean_name(match.group("name"))
    age = int(match.group("age"))
    if age < MIN_AGE or age > MAX_AGE:
        raise RegistrationError(f"Yas {MIN_AGE}-{MAX_AGE} arasinda olmali.")
    return name, age


def channel_matches_registration(channel):
    if not channel:
        return False
    normalized = normalize_text(channel.name)
    return normalized in DEFAULT_REGISTER_ALIASES or normalized.endswith("-kayit") or "kayit" in normalized


def is_registration_channel(message):
    if not message.guild or not message.channel:
        return False

    enabled = get_guild_setting(message.guild.id, "registration_enabled")
    if enabled is False:
        return False

    configured_channel_id = get_guild_setting(message.guild.id, "registration_channel_id")
    if configured_channel_id:
        try:
            return int(configured_channel_id) == message.channel.id
        except (TypeError, ValueError):
            return False

    return channel_matches_registration(message.channel)


def age_role_candidates(age):
    age_text = str(age)
    return {
        age_text,
        f"{age_text}+",
        f"+{age_text}",
        f"{age_text} yas",
        f"{age_text} yas rol",
        f"yas {age_text}",
        f"{age_text} yaş",
        f"{age_text} yaş rol",
        f"yaş {age_text}"
    }


def find_role_by_names(guild, names):
    exact = {item.lower() for item in names}
    normalized_names = {normalize_text(item) for item in names}

    for role in guild.roles:
        if role.name.lower() in exact:
            return role

    for role in guild.roles:
        if normalize_text(role.name) in normalized_names:
            return role

    return None


def find_age_role(guild, age):
    return find_role_by_names(guild, age_role_candidates(age))


def find_default_member_role(guild):
    role_id = get_guild_setting(guild.id, "registration_registered_role_id")
    if role_id:
        role = guild.get_role(int(role_id))
        if role:
            return role
    return find_role_by_names(guild, DEFAULT_MEMBER_ROLE_NAMES)


async def ensure_age_role(guild, age):
    role = find_age_role(guild, age)
    if role:
        return role, False, None

    auto_create = get_guild_setting(guild.id, "registration_create_age_roles", True)
    if not auto_create:
        return None, False, "Yas rolu bulunamadi ve otomatik rol olusturma kapali."

    if not guild.me.guild_permissions.manage_roles:
        return None, False, "Botta Manage Roles yetkisi yok, yas rolu olusturulamadi."

    try:
        role = await guild.create_role(
            name=f"{age} Yas",
            reason="NEXOS kayit yas rolu otomatik olusturma"
        )
        await log_event(
            guild,
            with_emoji("register", "Kayit Yas Rolu Olusturuldu"),
            f"`{role.name}` rolu otomatik olusturuldu.",
            0x8B5CF6,
            [("Yas", str(age)), ("Rol", f"{role.mention} ({role.id})")],
            log_type="mod"
        )
        return role, True, None
    except discord.HTTPException as error:
        return None, False, f"Yas rolu olusturulamadi: {error}"


async def add_safe_role(member, role, label):
    if not role:
        return False, None

    error = role_hierarchy_error(member.guild, None, member.guild.me, role, check_actor=False)
    error = error or self_assign_role_permission_error(role, label)
    if error:
        return False, error

    if role in member.roles:
        return False, None

    try:
        await member.add_roles(role, reason=f"NEXOS kayit: {label}")
        return True, None
    except discord.HTTPException as error:
        return False, f"{label} verilemedi: {error}"


async def set_member_nickname(member, nickname):
    if member.id == member.guild.owner_id:
        return False, "Sunucu sahibinin takma adi bot tarafindan degistirilemez."
    if not member.guild.me.guild_permissions.manage_nicknames:
        return False, "Botta Manage Nicknames yetkisi yok."
    if member.top_role >= member.guild.me.top_role:
        return False, "Uyenin rolu botun rolunden yukarida veya ayni seviyede."

    try:
        await member.edit(nick=nickname, reason="NEXOS kayit nick guncelleme")
        return True, None
    except discord.HTTPException as error:
        return False, f"Takma ad degistirilemedi: {error}"


async def send_registration_hint(message, error):
    embed = make_embed(
        with_emoji("register", "Kayit Formati"),
        f"{error}\n\nDogru format: `Isim | Yas`",
        0xE67E22
    )
    try:
        await message.channel.send(embed=embed, reference=message, delete_after=15)
    except discord.HTTPException:
        return False
    return True


async def process_registration_message(message):
    if message.author.bot or not message.guild:
        return False
    if not is_registration_channel(message):
        return False
    if not isinstance(message.author, discord.Member):
        return False

    member = message.author
    try:
        name, age = parse_registration_content(message.content)
    except RegistrationError as error:
        await send_registration_hint(message, str(error))
        await log_event(
            message.guild,
            with_emoji("register", "Kayit Formati Hatali"),
            f"{member.mention} kayit kanalinda hatali format kullandi.",
            0xE67E22,
            [
                ("Uye", f"{member} ({member.id})"),
                ("Kanal", f"{message.channel.mention} ({message.channel.id})"),
                ("Mesaj", trim(message.content or "Bos mesaj"))
            ],
            log_type="member"
        )
        return True

    errors = []
    age_role, age_role_created, age_role_error = await ensure_age_role(message.guild, age)
    if age_role_error:
        errors.append(age_role_error)

    age_added, age_add_error = await add_safe_role(member, age_role, "Yas rolu")
    if age_add_error:
        errors.append(age_add_error)

    registered_role = find_default_member_role(message.guild)
    registered_added, registered_error = await add_safe_role(member, registered_role, "Kayit rolu")
    if registered_error:
        errors.append(registered_error)

    nickname_set, nickname_error = await set_member_nickname(member, name)
    if nickname_error:
        errors.append(nickname_error)

    status = "partial" if errors else "completed"
    upsert_registration_record(
        message.guild.id,
        member.id,
        message.channel.id,
        message.id,
        name,
        age,
        age_role.id if age_role else None,
        registered_role.id if registered_role else None,
        nickname_set=nickname_set,
        status=status,
        errors=errors
    )

    color = 0x2ECC71 if not errors else 0xE67E22
    role_lines = []
    if age_role:
        role_lines.append(age_role.mention)
    if registered_role:
        role_lines.append(registered_role.mention)
    role_text = ", ".join(role_lines) if role_lines else "Rol bulunamadi"
    description = f"{member.mention} kaydi alindi.\nIsim: **{name}**\nYas: **{age}**\nRoller: {role_text}"
    if errors:
        description += "\n\nEksikler loga yazildi."

    try:
        await message.channel.send(embed=make_embed(with_emoji("register", "Kayit Tamamlandi"), description, color))
    except discord.HTTPException:
        pass

    await log_event(
        message.guild,
        with_emoji("register", "Kayit Tamamlandi" if not errors else "Kayit Kismi Tamamlandi"),
        description,
        color,
        [
            ("Uye", f"{member} ({member.id})"),
            ("Isim", name),
            ("Yas", str(age)),
            ("Yas Rolu", f"{age_role} ({age_role.id})" if age_role else "Yok"),
            ("Kayit Rolu", f"{registered_role} ({registered_role.id})" if registered_role else "Yok"),
            ("Yas Rolu Yeni Mi", "Evet" if age_role_created else "Hayir"),
            ("Nick Degisti", "Evet" if nickname_set else "Hayir"),
            ("Hatalar", "\n".join(errors) if errors else "Yok")
        ],
        log_type="member"
    )
    return True
