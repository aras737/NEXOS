import inspect
import traceback

from discord import app_commands

from core.embeds import make_embed


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

    if isinstance(error, app_commands.MissingPermissions):
        message = "Bu komut icin yetkin yok."
        location = "Kullanici yetkisi kontrolu"
    elif isinstance(error, app_commands.BotMissingPermissions):
        message = "Bu islem icin botun gerekli izni yok."
        location = "Bot yetkisi kontrolu"
    else:
        original = getattr(error, "original", error)
        message = "Komut calisirken hata olustu. Detayi DM olarak gonderdim."
        location = traceback_source(error)
        print("".join(traceback.format_exception(type(original), original, original.__traceback__)))

    dm_sent = await send_dm_error(
        interaction,
        "NEXOS Komut Hatasi",
        f"{name} komutunda hata yakalandi.",
        [
            ("Komut", name),
            ("Hata", message),
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
