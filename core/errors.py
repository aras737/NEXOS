import inspect
import traceback

from discord import app_commands

from core.embeds import make_embed
from core.logging import log_event


def command_name(interaction):
    if interaction.command:
        return f"/{interaction.command.name}"
    return f"/{interaction.data.get('name', 'bilinmiyor')}"


def command_source(interaction):
    if not interaction.command or not getattr(interaction.command, "callback", None):
        return "Komut kaynagi bulunamadi."

    try:
        file_path = inspect.getsourcefile(interaction.command.callback) or "bilinmiyor"
        _, start_line = inspect.getsourcelines(interaction.command.callback)
        return f"{file_path}:{start_line}"
    except OSError:
        return "Komut kaynagi okunamadi."


def traceback_source(error):
    original = getattr(error, "original", error)
    traceback_items = traceback.extract_tb(original.__traceback__)
    if not traceback_items:
        return "Traceback yok."

    last = traceback_items[-1]
    return f"{last.filename}:{last.lineno} -> {last.name}"


def error_detail(error):
    original = getattr(error, "original", error)
    detail = f"{type(original).__name__}: {original}"
    if detail.strip() == f"{type(original).__name__}:":
        return type(original).__name__
    return detail


async def send_interaction_error(interaction, message):
    embed = make_embed("Hata", message, 0xE74C3C)
    if interaction.response.is_done():
        await interaction.followup.send(embed=embed, ephemeral=True)
    else:
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def send_dm_error(interaction, title, description, fields):
    embed = make_embed(title, description, 0xE74C3C)
    for name, value in fields:
        embed.add_field(name=name, value=str(value)[:1024], inline=False)

    try:
        await interaction.user.send(embed=embed)
        return True
    except Exception:
        return False


async def handle_app_command_error(interaction, error):
    name = command_name(interaction)
    detail = error_detail(error)

    if isinstance(error, app_commands.MissingPermissions):
        message = "Bu komut icin gerekli yetkin yok."
        location = "Kullanici yetkisi kontrolu"
    elif isinstance(error, app_commands.BotMissingPermissions):
        message = "Bu islem icin botun gerekli Discord izni yok."
        location = "Bot yetkisi kontrolu"
    elif isinstance(error, app_commands.CommandOnCooldown):
        message = f"Bu komutu tekrar kullanmak icin {error.retry_after:.1f} saniye beklemelisin."
        location = "Komut cooldown kontrolu"
    elif isinstance(error, app_commands.CheckFailure):
        message = "Bu komut icin kontrol basarisiz oldu. Yetki, kanal veya bot iznini kontrol et."
        location = "Komut check kontrolu"
    elif isinstance(error, app_commands.TransformerError):
        message = "Komut parametrelerinden biri gecersiz. Secenekleri tekrar kontrol et."
        location = "Komut parametre donusumu"
    else:
        original = getattr(error, "original", error)
        if original.__class__.__name__ == "HTTPException":
            message = "Discord API istegi basarisiz oldu. Detayi DM ve log kanalina gonderdim."
        else:
            message = "Komut calisirken beklenmeyen hata olustu. Detayi DM ve log kanalina gonderdim."
        location = traceback_source(error)
        print("".join(traceback.format_exception(type(original), original, original.__traceback__)))

    dm_description = (
        f"{name} komutunda hata yakalandi.\n"
        "Bu rapor komutu duzeltmek icin gereken teknik bilgiyi icerir."
    )
    dm_sent = await send_dm_error(
        interaction,
        "NEXOS Hata Raporu",
        dm_description,
        [
            ("Komut", name),
            ("Hata", detail),
            ("Kullanici Mesaji", message),
            ("Komut Dosyasi", command_source(interaction)),
            ("Hatanin Geldigi Yer", location),
            ("Kullanan", f"{interaction.user} ({interaction.user.id})")
        ]
    )

    await log_event(
        interaction.guild,
        "Komut Hatasi",
        f"{name} komutunda hata yakalandi.",
        0xE74C3C,
        [
            ("Hata", detail),
            ("Komut Dosyasi", command_source(interaction)),
            ("Hatanin Geldigi Yer", location),
            ("Kullanan", f"{interaction.user} ({interaction.user.id})")
        ]
    )

    if dm_sent:
        await send_interaction_error(interaction, message)
    else:
        await send_interaction_error(
            interaction,
            f"{message}\nDM kapali oldugu icin detay gonderilemedi.\nKomut: {name}\nYer: {location}"
        )
