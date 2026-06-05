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


def required_permissions():
    return discord.Permissions(REQUIRED_PERMISSIONS_VALUE)


def invite_url(client_id):
    return discord.utils.oauth_url(
        client_id,
        permissions=required_permissions(),
        scopes=("bot", "applications.commands")
    )
