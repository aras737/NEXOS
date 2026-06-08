import discord

from core.emojis import with_emoji
from core.logging import log_event, trim


def user_label(user):
    return f"{user} ({user.id})"


def channel_label(channel):
    if not channel:
        return "Yok"
    mention = getattr(channel, "mention", None)
    return f"{mention or channel} ({channel.id})"


def role_list(roles):
    filtered = [role.mention for role in roles if not role.is_default()]
    return ", ".join(filtered) if filtered else "Yok"


def message_body(message):
    parts = []
    if message.content:
        parts.append(message.content)
    if message.attachments:
        parts.append("Ekler: " + ", ".join(attachment.url for attachment in message.attachments))
    if not parts:
        parts.append("Icerik yok veya Message Content Intent kapali.")
    return trim("\n".join(parts), 1000)


def channel_type(channel):
    return channel.__class__.__name__.replace("Channel", "")


async def audit_actor(guild, action, target_id=None):
    me = guild.me
    if not me or not me.guild_permissions.view_audit_log:
        return "Yok (View Audit Log yetkisi yok)"

    try:
        async for entry in guild.audit_logs(limit=8, action=action):
            target = getattr(entry, "target", None)
            if target_id is None or getattr(target, "id", None) == target_id:
                return user_label(entry.user) if entry.user else "Bilinmiyor"
    except discord.Forbidden:
        return "Yok (Audit Log erisimi reddedildi)"
    except discord.HTTPException:
        return "Yok (Audit Log okunamadi)"

    return "Bilinmiyor"


def changed_fields(before, after, names):
    changes = []
    for label, attr in names:
        old = getattr(before, attr, None)
        new = getattr(after, attr, None)
        if old != new:
            changes.append((label, f"{old} -> {new}"))
    return changes


async def log_message_delete(message):
    if not message.guild:
        return

    await log_event(
        message.guild,
        with_emoji("trash", "Mesaj Silindi"),
        f"{message.author} tarafindan gonderilen mesaj silindi.",
        0xE74C3C,
        [
            ("Kanal", channel_label(message.channel)),
            ("Yazan", user_label(message.author)),
            ("Mesaj ID", message.id),
            ("Icerik", message_body(message))
        ],
        log_type="message"
    )


async def log_message_edit(before, after):
    if not before.guild:
        return
    if before.content == after.content and len(before.attachments) == len(after.attachments):
        return

    await log_event(
        before.guild,
        with_emoji("edit", "Mesaj Duzenlendi"),
        f"{before.author} mesajini duzenledi.",
        0xF1C40F,
        [
            ("Kanal", channel_label(before.channel)),
            ("Yazan", user_label(before.author)),
            ("Mesaj ID", before.id),
            ("Eski Icerik", message_body(before)),
            ("Yeni Icerik", message_body(after))
        ],
        log_type="message"
    )


async def log_member_update(before, after):
    if before.nick != after.nick:
        await log_event(
            after.guild,
            with_emoji("member", "Uye Ismi Degisti"),
            f"{after.mention} sunucu adini degistirdi.",
            0x3498DB,
            [
                ("Uye", user_label(after)),
                ("Eski Isim", before.nick or before.name),
                ("Yeni Isim", after.nick or after.name)
            ],
            log_type="member"
        )

    before_roles = set(before.roles)
    after_roles = set(after.roles)
    added_roles = sorted(after_roles - before_roles, key=lambda role: role.position, reverse=True)
    removed_roles = sorted(before_roles - after_roles, key=lambda role: role.position, reverse=True)
    if added_roles or removed_roles:
        await log_event(
            after.guild,
            with_emoji("role", "Uye Rolleri Guncellendi"),
            f"{after.mention} uyesinin rolleri degisti.",
            0x9B59B6,
            [
                ("Uye", user_label(after)),
                ("Eklenen Roller", role_list(added_roles)),
                ("Alinan Roller", role_list(removed_roles))
            ],
            log_type="mod"
        )

    before_timeout = getattr(before, "timed_out_until", None)
    after_timeout = getattr(after, "timed_out_until", None)
    if before_timeout != after_timeout:
        await log_event(
            after.guild,
            with_emoji("shield", "Uye Timeout Durumu"),
            f"{after.mention} timeout durumu degisti.",
            0xE67E22,
            [
                ("Uye", user_label(after)),
                ("Eski", before_timeout or "Yok"),
                ("Yeni", after_timeout or "Yok")
            ],
            log_type="punishment"
        )


async def log_channel_create(channel):
    if not channel.guild:
        return
    actor = await audit_actor(channel.guild, discord.AuditLogAction.channel_create, channel.id)

    await log_event(
        channel.guild,
        with_emoji("channel", "Kanal Olusturuldu"),
        f"{channel_type(channel)} kanali olusturuldu.",
        0x2ECC71,
        [
            ("Kanal", channel_label(channel)),
            ("Kategori", getattr(getattr(channel, "category", None), "name", "Yok")),
            ("Tip", channel_type(channel)),
            ("Yapan", actor)
        ],
        log_type="mod"
    )


async def log_channel_delete(channel):
    if not channel.guild:
        return
    actor = await audit_actor(channel.guild, discord.AuditLogAction.channel_delete, channel.id)

    await log_event(
        channel.guild,
        with_emoji("trash", "Kanal Silindi"),
        f"{channel_type(channel)} kanali silindi.",
        0xE74C3C,
        [
            ("Kanal", f"{channel} ({channel.id})"),
            ("Kategori", getattr(getattr(channel, "category", None), "name", "Yok")),
            ("Tip", channel_type(channel)),
            ("Yapan", actor)
        ],
        log_type="mod"
    )


async def log_channel_update(before, after):
    changes = changed_fields(
        before,
        after,
        [
            ("Isim", "name"),
            ("Konu", "topic"),
            ("Yavas Mod", "slowmode_delay"),
            ("NSFW", "nsfw"),
            ("Bitrate", "bitrate"),
            ("Kullanici Limiti", "user_limit")
        ]
    )
    if not changes:
        return
    actor = await audit_actor(after.guild, discord.AuditLogAction.channel_update, after.id)

    await log_event(
        after.guild,
        with_emoji("settings", "Kanal Guncellendi"),
        f"{channel_label(after)} ayarlari degisti.",
        0x3498DB,
        [("Kanal", channel_label(after)), ("Yapan", actor), *changes],
        log_type="mod"
    )


async def log_role_create(role):
    actor = await audit_actor(role.guild, discord.AuditLogAction.role_create, role.id)
    await log_event(
        role.guild,
        with_emoji("role", "Rol Olusturuldu"),
        f"{role.mention} rolu olusturuldu.",
        0x2ECC71,
        [
            ("Rol", f"{role} ({role.id})"),
            ("Renk", str(role.color)),
            ("Pozisyon", role.position),
            ("Yapan", actor)
        ],
        log_type="mod"
    )


async def log_role_delete(role):
    actor = await audit_actor(role.guild, discord.AuditLogAction.role_delete, role.id)
    await log_event(
        role.guild,
        with_emoji("trash", "Rol Silindi"),
        f"{role} rolu silindi.",
        0xE74C3C,
        [
            ("Rol", f"{role} ({role.id})"),
            ("Renk", str(role.color)),
            ("Pozisyon", role.position),
            ("Yapan", actor)
        ],
        log_type="mod"
    )


async def log_role_update(before, after):
    changes = changed_fields(
        before,
        after,
        [
            ("Isim", "name"),
            ("Renk", "color"),
            ("Ayrik Goster", "hoist"),
            ("Etiketlenebilir", "mentionable"),
            ("Pozisyon", "position")
        ]
    )
    if before.permissions.value != after.permissions.value:
        changes.append(("Yetki Degeri", f"{before.permissions.value} -> {after.permissions.value}"))
    if not changes:
        return
    actor = await audit_actor(after.guild, discord.AuditLogAction.role_update, after.id)

    await log_event(
        after.guild,
        with_emoji("role", "Rol Guncellendi"),
        f"{after.mention} rolu guncellendi.",
        0xF1C40F,
        [("Rol", f"{after} ({after.id})"), ("Yapan", actor), *changes],
        log_type="mod"
    )


async def log_voice_state_update(member, before, after):
    if before.channel != after.channel:
        if before.channel and after.channel:
            title = with_emoji("voice", "Ses Kanali Degisti")
            description = f"{member.mention} ses kanalini degistirdi."
            fields = [
                ("Uye", user_label(member)),
                ("Eski Kanal", channel_label(before.channel)),
                ("Yeni Kanal", channel_label(after.channel))
            ]
            color = 0x3498DB
        elif after.channel:
            title = with_emoji("voice", "Sese Katildi")
            description = f"{member.mention} ses kanalina katildi."
            fields = [("Uye", user_label(member)), ("Kanal", channel_label(after.channel))]
            color = 0x2ECC71
        else:
            title = with_emoji("voice", "Sesten Ayrildi")
            description = f"{member.mention} ses kanalindan ayrildi."
            fields = [("Uye", user_label(member)), ("Kanal", channel_label(before.channel))]
            color = 0xE67E22

        await log_event(member.guild, title, description, color, fields, log_type="voice")

    changes = []
    voice_flags = [
        ("Sunucu Mute", "mute"),
        ("Sunucu Deaf", "deaf"),
        ("Kendi Mute", "self_mute"),
        ("Kendi Deaf", "self_deaf"),
        ("Kamera", "self_video"),
        ("Yayin", "self_stream")
    ]
    for label, attr in voice_flags:
        old = getattr(before, attr, None)
        new = getattr(after, attr, None)
        if old != new:
            changes.append((label, f"{old} -> {new}"))

    if changes:
        await log_event(
            member.guild,
            with_emoji("mute", "Ses Durumu Degisti"),
            f"{member.mention} ses durumu degisti.",
            0x9B59B6,
            [("Uye", user_label(member)), *changes],
            log_type="voice"
        )


async def log_member_ban(guild, user):
    actor = await audit_actor(guild, discord.AuditLogAction.ban, user.id)
    await log_event(
        guild,
        with_emoji("ban", "Uye Banlandi"),
        f"{user} sunucudan banlandi.",
        0xE74C3C,
        [("Uye", user_label(user)), ("Yapan", actor)],
        log_type="punishment"
    )


async def log_member_unban(guild, user):
    actor = await audit_actor(guild, discord.AuditLogAction.unban, user.id)
    await log_event(
        guild,
        with_emoji("unban", "Ban Kaldirildi"),
        f"{user} ban kaldirildi.",
        0x2ECC71,
        [("Uye", user_label(user)), ("Yapan", actor)],
        log_type="punishment"
    )


async def log_emojis_update(guild, before, after):
    before_by_id = {emoji.id: emoji for emoji in before}
    after_by_id = {emoji.id: emoji for emoji in after}
    added = [after_by_id[item] for item in after_by_id.keys() - before_by_id.keys()]
    removed = [before_by_id[item] for item in before_by_id.keys() - after_by_id.keys()]
    renamed = [
        (before_by_id[item], after_by_id[item])
        for item in before_by_id.keys() & after_by_id.keys()
        if before_by_id[item].name != after_by_id[item].name
    ]

    if not added and not removed and not renamed:
        return

    fields = []
    if added:
        fields.append(("Eklenen Emojiler", ", ".join(f"{emoji} `{emoji.name}`" for emoji in added)))
    if removed:
        fields.append(("Silinen Emojiler", ", ".join(f"`{emoji.name}` ({emoji.id})" for emoji in removed)))
    if renamed:
        fields.append(("Adi Degisen Emojiler", ", ".join(f"`{old.name}` -> `{new.name}`" for old, new in renamed)))

    await log_event(
        guild,
        with_emoji("emoji", "Emoji Guncellendi"),
        "Sunucu emoji listesi degisti.",
        0xF1C40F,
        fields,
        log_type="mod"
    )


async def log_guild_join(guild):
    await log_event(
        guild,
        with_emoji("rocket", "NEXOS Sunucuya Katildi"),
        f"NEXOS {guild.name} sunucusuna katildi.",
        0x2ECC71,
        [
            ("Sunucu", f"{guild.name} ({guild.id})"),
            ("Uye Sayisi", guild.member_count or "Bilinmiyor")
        ],
        log_type="general"
    )


async def log_guild_remove(guild):
    print(f"NEXOS sunucudan ayrildi: {guild.name} ({guild.id})")
