EMOJIS = {
    "ok": "✅",
    "error": "❌",
    "warn": "⚠️",
    "info": "ℹ️",
    "galaxy": "🌌",
    "spark": "✨",
    "star": "⭐",
    "wave": "👋",
    "rocket": "🚀",
    "shield": "🛡️",
    "bot": "🤖",
    "member": "👤",
    "join": "📥",
    "leave": "📤",
    "message": "💬",
    "edit": "✏️",
    "trash": "🗑️",
    "role": "🎭",
    "channel": "📺",
    "voice": "🔊",
    "mute": "🔇",
    "music": "🎵",
    "emoji": "😀",
    "ticket": "🎫",
    "giveaway": "🎉",
    "gift": "🎁",
    "register": "✅",
    "coin": "🪙",
    "lock": "🔒",
    "unlock": "🔓",
    "settings": "⚙️",
    "server": "🏠",
    "count": "🔢",
    "ban": "🔨",
    "unban": "🕊️",
    "crown": "👑"
}


def emoji(key, fallback=""):
    return EMOJIS.get(key, fallback)


def with_emoji(key, text):
    icon = emoji(key)
    return f"{icon} {text}" if icon else text
