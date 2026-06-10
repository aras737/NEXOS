import datetime
from collections import defaultdict

import discord

from core.embeds import make_embed
from core.emojis import with_emoji
from core.logging import log_event, trim
from core.permissions import role_hierarchy_error
from core.storage import get_guild_setting, set_guild_setting


SECURITY_EVENTS = defaultdict(list)
AUDIT_MAX_AGE = datetime.timedelta(seconds=25)
DANGEROUS_PERMISSIONS = (
    "administrator",
    "manage_guild",
    "manage_roles",
    "manage_channels",
    "manage_webhooks",
    "manage_messages",
    "kick_members",
    "ban_members",
    "moderate_members"
)


def security_enabled(guild_id):
    return get_guild_setting(guild_id, "security_enabled", True) is not False


def bot_guard_enabled(guild_id):
    return get_guild_setting(guild_id, "security_bot_guard_enabled", True) is not False


def anti_raid_enabled(guild_id):
    return get_guild_setting(guild_id, "security_anti_raid_enabled", True) is not False


def security_setting(guild_id, key, default):
    return get_guild_setting(guild_id, f"security_{key}", default)


def allowed_bot_ids(guild_id):
    values = get_guild_setting(guild_id, "security_allowed_bot_ids", [])
    if not isinstance(values, list):
        return []
    return [int(item) for item in values if str(item).isdigit()]


def add_allowed_bot(guild_id, bot_id):
    bot_id = int(bot_id)
    values = allowed_bot_ids(guild_id)
    if bot_id not in values:
        values.append(bot_id)
    set_guild_setting(guild_id, "security_allowed_bot_ids", values)
    return values


def remove_allowed_bot(guild_id, bot_id):
    bot_id = int(bot_id)
    values = [item for item in allowed_bot_ids(guild_id) if int(item) != bot_id]
    set_guild_setting(guild_id, "security_allowed_bot_ids", values)
    return values


def dangerous_role(role):
    if role.is_default() or role.managed:
        return False
    return any(getattr(role.permissions, permission, False) for permission in DANGEROUS_PERMISSIONS)


async def fetch_member_safe(guild, user_id):
    if not user_id:
        return None
    member = guild.get_member(int(user_id))
    if member:
        return member
    try:
        return await guild.fetch_member(int(user_id))
    except (discord.HTTPException, discord.NotFound):
        return None


async def recent_audit_entry(guild, action, target_id=None, max_age=AUDIT_MAX_AGE):
    if not action:
        return None
    me = guild.me
    if not me or not me.guild_permissions.view_audit_log:
        return None

    now = datetime.datetime.now(datetime.timezone.utc)
    try:
        async for entry in guild.audit_logs(limit=10, action=action):
            if max_age and now - entry.created_at > max_age:
                continue
            target = getattr(entry, "target", None)
            if target_id is None or getattr(target, "id", None) == int(target_id):
                return entry
    except (discord.Forbidden, discord.HTTPException):
        return None
    return None


async def strip_dangerous_roles(member, reason):
    if not member:
        return [], ["Uye bulunamadi veya artik sunucuda degil."]
    if member.id == member.guild.owner_id:
        return [], ["Sunucu sahibinden yetki alinamaz."]
    if not member.guild.me.guild_permissions.manage_roles:
        return [], ["Botta Manage Roles yetkisi yok."]

    removed = []
    skipped = []
    for role in sorted(member.roles, key=lambda item: item.position, reverse=True):
        if not dangerous_role(role):
            continue
        hierarchy_error = role_hierarchy_error(member.guild, None, member.guild.me, role, check_actor=False)
        if hierarchy_error:
            skipped.append(f"{role.name}: {hierarchy_error}")
            continue
        try:
            await member.remove_roles(role, reason=reason)
            removed.append(role)
        except discord.HTTPException as error:
            skipped.append(f"{role.name}: {error}")
    return removed, skipped


async def notify_owner(guild, embed, view=None):
    owner = guild.owner or await fetch_member_safe(guild, guild.owner_id)
    if not owner:
        return False
    try:
        await owner.send(embed=embed, view=view)
        return True
    except discord.HTTPException:
        return False


def user_text(user):
    if not user:
        return "Bilinmiyor"
    return f"{user} ({user.id})"


def role_names(roles):
    return ", ".join(role.mention for role in roles) if roles else "Yok"


class BotGuardReviewView(discord.ui.View):
    def __init__(self, guild_id, bot_id, actor_id):
        super().__init__(timeout=86400)
        self.guild_id = int(guild_id)
        self.bot_id = int(bot_id)
        self.actor_id = int(actor_id) if actor_id else None

    async def guard_owner(self, interaction):
        guild = interaction.client.get_guild(self.guild_id)
        if not guild:
            await interaction.response.send_message("Sunucu bulunamadi.", ephemeral=True)
            return None
        if interaction.user.id != guild.owner_id:
            await interaction.response.send_message("Bu paneli sadece sunucu sahibi kullanabilir.", ephemeral=True)
            return None
        return guild

    @discord.ui.button(label="Onayla", style=discord.ButtonStyle.success)
    async def approve(self, interaction, button):
        guild = await self.guard_owner(interaction)
        if not guild:
            return
        add_allowed_bot(guild.id, self.bot_id)
        await log_event(
            guild,
            with_emoji("shield", "Bot Allowlist Onayi"),
            f"`{self.bot_id}` ID'li bot sunucu sahibi tarafindan allowlist'e alindi.",
            0x2ECC71,
            [("Onaylayan", user_text(interaction.user))],
            log_type="mod"
        )
        await interaction.response.edit_message(
            embed=make_embed("Bot Onaylandi", f"`{self.bot_id}` artik tekrar eklenirse izinli sayilacak.", 0x2ECC71),
            view=None
        )

    @discord.ui.button(label="Reddet", style=discord.ButtonStyle.danger)
    async def deny(self, interaction, button):
        guild = await self.guard_owner(interaction)
        if not guild:
            return
        remove_allowed_bot(guild.id, self.bot_id)
        await log_event(
            guild,
            with_emoji("shield", "Bot Ekleme Reddedildi"),
            f"`{self.bot_id}` ID'li bot reddedildi.",
            0xE74C3C,
            [("Reddeden", user_text(interaction.user))],
            log_type="mod"
        )
        await interaction.response.edit_message(
            embed=make_embed("Bot Reddedildi", f"`{self.bot_id}` allowlist'e alinmadi.", 0xE74C3C),
            view=None
        )

    @discord.ui.button(label="Yetki Al", style=discord.ButtonStyle.secondary)
    async def take_permissions(self, interaction, button):
        guild = await self.guard_owner(interaction)
        if not guild:
            return
        actor = await fetch_member_safe(guild, self.actor_id)
        removed, skipped = await strip_dangerous_roles(actor, "NEXOS bot ekleme korumasi")
        await log_event(
            guild,
            with_emoji("shield", "Bot Ekleyenin Yetkileri Alindi"),
            f"{actor.mention if actor else 'Bilinmeyen uye'} icin tehlikeli roller temizlendi.",
            0xF59E0B,
            [
                ("Islem Yapan", user_text(interaction.user)),
                ("Yetkisi Alinan", user_text(actor)),
                ("Alinan Roller", role_names(removed)),
                ("Atlanan", "\n".join(skipped) if skipped else "Yok")
            ],
            log_type="mod"
        )
        await interaction.response.send_message("Yetki alma denemesi tamamlandi.", ephemeral=True)


async def handle_bot_join(member):
    if not member.bot or not member.guild:
        return False

    guild = member.guild
    if guild.me and member.id == guild.me.id:
        return True

    if not security_enabled(guild.id) or not bot_guard_enabled(guild.id):
        return True

    if member.id in allowed_bot_ids(guild.id):
        await log_event(
            guild,
            with_emoji("shield", "Izinli Bot Eklendi"),
            f"{member.mention} allowlist'te oldugu icin sunucuda kaldi.",
            0x2ECC71,
            [("Bot", user_text(member))],
            log_type="mod"
        )
        return True

    action = getattr(discord.AuditLogAction, "bot_add", None)
    entry = await recent_audit_entry(guild, action, member.id)
    actor = await fetch_member_safe(guild, entry.user.id) if entry and entry.user else None

    kicked = False
    kick_error = None
    if guild.me.guild_permissions.kick_members:
        try:
            await member.kick(reason="NEXOS bot ekleme korumasi: allowlist disi bot")
            kicked = True
        except discord.HTTPException as error:
            kick_error = str(error)
    else:
        kick_error = "Botta Kick Members yetkisi yok."

    removed, skipped = await strip_dangerous_roles(actor, "NEXOS izinsiz bot ekleme korumasi")

    embed = make_embed(
        with_emoji("shield", "Izinsiz Bot Ekleme Engellendi"),
        f"{member} sunucuya eklendi fakat allowlist'te olmadigi icin engellendi.",
        0xE74C3C
    )
    embed.add_field(name="Bot", value=user_text(member), inline=False)
    embed.add_field(name="Ekleyen", value=user_text(actor or (entry.user if entry else None)), inline=False)
    embed.add_field(name="Bot Atildi", value="Evet" if kicked else f"Hayir: {kick_error}", inline=False)
    embed.add_field(name="Alinan Roller", value=role_names(removed), inline=False)
    embed.add_field(name="Atlanan", value=trim("\n".join(skipped) if skipped else "Yok", 1000), inline=False)
    embed.set_footer(text="Onayla: botu allowlist'e alir. Reddet: izin vermez. Yetki Al: ekleyenin tehlikeli rollerini tekrar temizler.")

    await log_event(
        guild,
        with_emoji("shield", "Izinsiz Bot Ekleme Engellendi"),
        f"{member} allowlist disi oldugu icin engellendi.",
        0xE74C3C,
        [
            ("Bot", user_text(member)),
            ("Ekleyen", user_text(actor or (entry.user if entry else None))),
            ("Bot Atildi", "Evet" if kicked else f"Hayir: {kick_error}"),
            ("Alinan Roller", role_names(removed)),
            ("Atlanan", "\n".join(skipped) if skipped else "Yok")
        ],
        log_type="mod"
    )
    await notify_owner(guild, embed, BotGuardReviewView(guild.id, member.id, actor.id if actor else 0))
    return True


def guard_event_key(action_key):
    if action_key in {"channel_delete", "role_delete"}:
        return "delete"
    if action_key in {"ban", "kick"}:
        return "punishment"
    return "change"


async def handle_guarded_audit_event(guild, action_key, audit_action, target_id, title, description):
    if not guild or not security_enabled(guild.id) or not anti_raid_enabled(guild.id):
        return False

    entry = await recent_audit_entry(guild, audit_action, target_id)
    bot_id = guild.me.id if guild.me else None
    if not entry or not entry.user or entry.user.id in {guild.owner_id, bot_id}:
        return False

    actor = await fetch_member_safe(guild, entry.user.id)
    if not actor:
        return False

    threshold = int(security_setting(guild.id, "raid_threshold", 3))
    window = int(security_setting(guild.id, "raid_window_seconds", 30))
    now = datetime.datetime.now(datetime.timezone.utc)
    key = (guild.id, actor.id, guard_event_key(action_key))
    events = [item for item in SECURITY_EVENTS[key] if (now - item).total_seconds() <= window]
    events.append(now)
    SECURITY_EVENTS[key] = events

    await log_event(
        guild,
        with_emoji("shield", title),
        description,
        0xF59E0B,
        [
            ("Yapan", user_text(actor)),
            ("Aksiyon", action_key),
            ("Pencere", f"{len(events)}/{threshold} olay, {window} sn")
        ],
        log_type="mod"
    )

    if len(events) < threshold:
        return False

    removed, skipped = await strip_dangerous_roles(actor, f"NEXOS anti-raid: {action_key}")
    alert = make_embed(
        with_emoji("shield", "Sunucu Koruma Alarmi"),
        f"{actor.mention} kisa surede cok fazla kritik islem yapti.",
        0xE74C3C
    )
    alert.add_field(name="Aksiyon", value=action_key, inline=True)
    alert.add_field(name="Olay Sayisi", value=str(len(events)), inline=True)
    alert.add_field(name="Alinan Roller", value=role_names(removed), inline=False)
    alert.add_field(name="Atlanan", value=trim("\n".join(skipped) if skipped else "Yok", 1000), inline=False)
    await notify_owner(guild, alert)
    await log_event(
        guild,
        with_emoji("shield", "Sunucu Koruma Yetki Aldi"),
        f"{actor.mention} icin anti-raid yetki alma denemesi yapildi.",
        0xE74C3C,
        [
            ("Yapan", user_text(actor)),
            ("Aksiyon", action_key),
            ("Alinan Roller", role_names(removed)),
            ("Atlanan", "\n".join(skipped) if skipped else "Yok")
        ],
        log_type="mod"
    )
    return True
