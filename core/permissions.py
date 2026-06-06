import discord


REQUIRED_PERMISSION_LABELS = [
    "View Channels",
    "Send Messages",
    "Embed Links",
    "Read Message History",
    "Use Application Commands",
    "Manage Messages",
    "Manage Channels",
    "Manage Roles",
    "Kick Members",
    "Ban Members",
    "Moderate Members",
    "Connect",
    "Speak"
]

REQUIRED_PERMISSIONS_VALUE = 1101930785814

DANGEROUS_SELF_ROLE_PERMISSIONS = {
    "administrator": "Administrator",
    "manage_guild": "Manage Server",
    "manage_roles": "Manage Roles",
    "manage_channels": "Manage Channels",
    "manage_messages": "Manage Messages",
    "kick_members": "Kick Members",
    "ban_members": "Ban Members",
    "moderate_members": "Moderate Members"
}


def required_permissions():
    return discord.Permissions(REQUIRED_PERMISSIONS_VALUE)


def invite_url(client_id):
    return discord.utils.oauth_url(
        client_id,
        permissions=required_permissions(),
        scopes=("bot", "applications.commands")
    )


def role_hierarchy_error(guild, actor, bot_member, role, check_actor=True):
    if role.is_default():
        return "@everyone rolu bu islem icin kullanilamaz."
    if role.managed:
        return "Entegrasyon/bot tarafindan yonetilen roller verilemez."
    if bot_member and role >= bot_member.top_role:
        return "Bu rol botun rolunden yukarida veya ayni seviyede. Bot bu rolu veremez."
    if check_actor and actor and actor.id != guild.owner_id and role >= actor.top_role:
        return "Bu rol senin en yuksek rolunden yukarida veya ayni seviyede."
    return None


def member_hierarchy_error(guild, actor, bot_member, member):
    if member.id == guild.owner_id:
        return "Sunucu sahibine rol islemi uygulanamaz."
    if bot_member and member.top_role >= bot_member.top_role:
        return "Bu uyenin rolu botun rolunden yukarida veya ayni seviyede."
    if actor and actor.id != guild.owner_id and member.top_role >= actor.top_role:
        return "Bu uyenin rolu senin rolunden yukarida veya ayni seviyede."
    return None


def self_assign_role_permission_error(role, action_label="Butonla alinacak rol"):
    permissions = role.permissions
    blocked = []
    for key, label in DANGEROUS_SELF_ROLE_PERMISSIONS.items():
        if getattr(permissions, key, False):
            blocked.append(label)
    if blocked:
        return f"{action_label} guvenli olmali. Bu rolde tehlikeli yetkiler var: {', '.join(blocked)}."
    return None
