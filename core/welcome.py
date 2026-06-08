import io
import random

import discord

from core.embeds import make_embed
from core.emojis import with_emoji
from core.storage import get_guild_setting

try:
    from PIL import Image, ImageDraw, ImageFont, ImageOps
except ImportError:
    Image = None
    ImageDraw = None
    ImageFont = None
    ImageOps = None


WELCOME_COLOR = 0x8B5CF6
LEAVE_COLOR = 0x34495E

DEFAULT_WELCOME_MESSAGE = (
    "🌌 {mention}, NEXOS galaksisine hos geldin. Yildiz rotan {server} sunucusunda basladi; "
    "artik {count}. uyemizsin. ✨"
)
DEFAULT_LEAVE_MESSAGE = "📤 {user} galaksiden ayrildi. {server} artik {count} uyeye sahip."


def load_font(size, bold=False):
    if not ImageFont:
        return None

    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf"
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def text_width(draw, text, font):
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0]


def trim_to_width(draw, text, font, max_width):
    text = str(text)
    if text_width(draw, text, font) <= max_width:
        return text

    while text and text_width(draw, text + "...", font) > max_width:
        text = text[:-1]
    return text + "..." if text else "..."


def resample_filter():
    if hasattr(Image, "Resampling"):
        return Image.Resampling.LANCZOS
    return Image.LANCZOS


async def member_avatar_image(member, size):
    if not Image:
        return None

    try:
        data = await member.display_avatar.replace(size=256).read()
        avatar = Image.open(io.BytesIO(data)).convert("RGBA")
        avatar = ImageOps.fit(avatar, (size, size), method=resample_filter())
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
        avatar.putalpha(mask)
        return avatar
    except Exception:
        return None


async def build_welcome_card(member):
    if not Image:
        return None

    width, height = 1100, 420
    image = Image.new("RGBA", (width, height), (12, 16, 32, 255))
    draw = ImageDraw.Draw(image)

    for y in range(height):
        ratio = y / height
        r = int(18 + ratio * 54)
        g = int(20 + ratio * 22)
        b = int(48 + ratio * 70)
        draw.line((0, y, width, y), fill=(r, g, b, 255))

    rng = random.Random(member.id + member.guild.id)
    for _ in range(95):
        x = rng.randint(0, width - 1)
        y = rng.randint(0, height - 1)
        radius = rng.choice([1, 1, 2, 2, 3])
        alpha = rng.randint(110, 230)
        color = rng.choice([(255, 255, 255, alpha), (168, 139, 250, alpha), (94, 234, 212, alpha)])
        draw.ellipse((x, y, x + radius, y + radius), fill=color)

    draw.rounded_rectangle((36, 34, width - 36, height - 34), radius=34, outline=(167, 139, 250, 160), width=3)
    draw.rounded_rectangle((60, 60, width - 60, height - 60), radius=28, fill=(9, 13, 28, 136))
    draw.ellipse((770, -150, 1180, 260), fill=(124, 58, 237, 70))
    draw.ellipse((820, 170, 1080, 430), fill=(45, 212, 191, 42))

    avatar_size = 168
    avatar_x, avatar_y = 88, 126
    draw.ellipse((avatar_x - 9, avatar_y - 9, avatar_x + avatar_size + 9, avatar_y + avatar_size + 9), fill=(167, 139, 250, 220))
    avatar = await member_avatar_image(member, avatar_size)
    if avatar:
        image.alpha_composite(avatar, (avatar_x, avatar_y))
    else:
        draw.ellipse((avatar_x, avatar_y, avatar_x + avatar_size, avatar_y + avatar_size), fill=(88, 101, 242, 255))

    title_font = load_font(52, bold=True)
    subtitle_font = load_font(28, bold=True)
    body_font = load_font(25)
    small_font = load_font(22)

    text_x = 300
    display_name = trim_to_width(draw, member.display_name.upper(), title_font, 690)
    server_name = trim_to_width(draw, member.guild.name, body_font, 520)
    member_count = member.guild.member_count or len(member.guild.members)

    draw.text((text_x, 108), "MERHABA", font=subtitle_font, fill=(94, 234, 212, 255))
    draw.text((text_x, 146), display_name, font=title_font, fill=(255, 255, 255, 255))
    draw.text((text_x, 214), "NEXOS GALAKSISINE HOS GELDIN", font=body_font, fill=(216, 180, 254, 255))

    badge_y = 275
    draw.rounded_rectangle((text_x, badge_y, text_x + 310, badge_y + 48), radius=18, fill=(88, 101, 242, 190))
    draw.text((text_x + 22, badge_y + 10), f"Sunucu: {server_name}", font=small_font, fill=(255, 255, 255, 255))
    draw.rounded_rectangle((text_x + 330, badge_y, text_x + 590, badge_y + 48), radius=18, fill=(20, 184, 166, 175))
    draw.text((text_x + 352, badge_y + 10), f"Uye sayisi: {member_count}", font=small_font, fill=(255, 255, 255, 255))

    draw.text((76, 360), "NEXOS WELCOME SYSTEM", font=small_font, fill=(203, 213, 225, 230))

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return discord.File(buffer, filename="nexos-welcome.png")


def render_member_text(template, member):
    guild = member.guild
    count = guild.member_count or len(guild.members)
    values = {
        "{mention}": member.mention,
        "{user}": str(member),
        "{name}": member.display_name,
        "{server}": guild.name,
        "{count}": str(count)
    }
    text = str(template or "")
    for key, value in values.items():
        text = text.replace(key, value)
    return text


def configured_text_channel(guild, key):
    channel_id = get_guild_setting(guild.id, key)
    if not channel_id:
        return None
    channel = guild.get_channel(int(channel_id))
    return channel if isinstance(channel, discord.TextChannel) else None


async def send_member_welcome(member):
    if get_guild_setting(member.guild.id, "welcome_enabled", True) is False:
        return False

    channel = configured_text_channel(member.guild, "welcome_channel_id") or member.guild.system_channel
    if not channel:
        return False

    message = get_guild_setting(member.guild.id, "welcome_message", DEFAULT_WELCOME_MESSAGE)
    embed = make_embed(
        with_emoji("galaxy", "NEXOS Galaksiye Hos Geldin"),
        render_member_text(message, member),
        WELCOME_COLOR
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="Sunucu", value=member.guild.name, inline=True)
    embed.add_field(name="Uye Sayisi", value=str(member.guild.member_count or len(member.guild.members)), inline=True)
    embed.set_footer(text="Galaksi kaydi basariyla tamamlandi. ✨")

    try:
        file = await build_welcome_card(member)
        if file:
            embed.set_image(url="attachment://nexos-welcome.png")
            await channel.send(content=member.mention, embed=embed, file=file)
        else:
            await channel.send(content=member.mention, embed=embed)
        return True
    except discord.HTTPException:
        return False


async def send_member_leave(member):
    if get_guild_setting(member.guild.id, "welcome_enabled", True) is False:
        return False

    channel = (
        configured_text_channel(member.guild, "leave_channel_id")
        or configured_text_channel(member.guild, "welcome_channel_id")
    )
    if not channel:
        return False

    message = get_guild_setting(member.guild.id, "leave_message", DEFAULT_LEAVE_MESSAGE)
    embed = make_embed(
        with_emoji("leave", "NEXOS Galaksi Cikisi"),
        render_member_text(message, member),
        LEAVE_COLOR
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="Sunucu", value=member.guild.name, inline=True)
    embed.add_field(name="Kalan Uye", value=str(member.guild.member_count or len(member.guild.members)), inline=True)

    try:
        await channel.send(embed=embed)
        return True
    except discord.HTTPException:
        return False
