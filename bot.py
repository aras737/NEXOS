import discord
from discord.ext import commands

from bot_commands import register_all_commands
from core.auto_role import ButtonRoleView, apply_auto_role
from core.config import DISCORD_TOKEN, GUILD_ID, VOICE_CHANNEL_ID
from core.emojis import with_emoji
from core.errors import handle_app_command_error
from core.event_logs import (
    log_channel_create,
    log_channel_delete,
    log_channel_update,
    log_emojis_update,
    log_guild_join,
    log_guild_remove,
    log_member_ban,
    log_member_unban,
    log_member_update,
    log_message_delete,
    log_message_edit,
    log_role_create,
    log_role_delete,
    log_role_update,
    log_voice_state_update
)
from core.logging import log_event, log_interaction
from core.member_counter import update_member_count_channel
from core.tickets import TicketControlView, TicketPanelView
from core.welcome import send_member_leave, send_member_welcome
from core.web_server import start_web_server


start_web_server()

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.voice_states = True
intents.messages = True
if hasattr(intents, "message_content"):
    intents.message_content = True
if hasattr(intents, "moderation"):
    intents.moderation = True


class NexosBot(commands.Bot):
    async def setup_hook(self):
        self.add_view(ButtonRoleView())
        self.add_view(TicketPanelView())
        self.add_view(TicketControlView())
        register_all_commands(self)

        if GUILD_ID:
            guild = discord.Object(id=GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            print(f"{len(synced)} slash komut GUILD_ID sunucusuna yuklendi.")
        else:
            synced = await self.tree.sync()
            print(f"{len(synced)} global slash komut yuklendi.")


bot = NexosBot(command_prefix="!", intents=intents, help_command=None)


@bot.event
async def on_ready():
    print(f"{bot.user} aktif. NEXOS slash moderasyon sistemi hazir.")
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{len(bot.guilds)} sunucu | NEXOS Galaksiyi İzliyor"
        )
    )

    for guild in bot.guilds:
        await log_event(
            guild,
            with_emoji("bot", "Bot Aktif"),
            "NEXOS baslatildi ve slash komut sistemi hazir.",
            0x2ECC71,
            [
                ("Sunucu Sayisi", str(len(bot.guilds))),
                ("Toplam Kullanici", str(sum(item.member_count or 0 for item in bot.guilds)))
            ]
        )

    if VOICE_CHANNEL_ID:
        try:
            channel = bot.get_channel(VOICE_CHANNEL_ID)
            if channel and isinstance(channel, discord.VoiceChannel):
                if not discord.utils.get(bot.voice_clients, guild=channel.guild):
                    await channel.connect()
                print(f"Ses kanalina baglandi: {channel.name}")
            else:
                print("VOICE_CHANNEL_ID gecerli bir ses kanali degil.")
        except Exception as error:
            print(f"Ses kanalina baglanirken hata olustu: {error}")

    for guild in bot.guilds:
        try:
            await update_member_count_channel(guild)
        except Exception as error:
            print(f"Uye sayaci guncellenirken hata olustu: {error}")


@bot.event
async def on_member_join(member):
    try:
        await update_member_count_channel(member.guild)
    except Exception as error:
        print(f"Uye sayaci guncellenirken hata olustu: {error}")

    await log_event(
        member.guild,
        with_emoji("join", "Uye Katildi"),
        f"{member.mention} sunucuya katildi.",
        0x2ECC71,
        [("Uye", f"{member} ({member.id})")]
    )
    await apply_auto_role(member)
    await send_member_welcome(member)


@bot.event
async def on_member_remove(member):
    try:
        await update_member_count_channel(member.guild)
    except Exception as error:
        print(f"Uye sayaci guncellenirken hata olustu: {error}")

    await log_event(
        member.guild,
        with_emoji("leave", "Uye Ayrildi"),
        f"{member} sunucudan ayrildi.",
        0xE67E22,
        [("Uye", f"{member} ({member.id})")]
    )
    await send_member_leave(member)


@bot.event
async def on_member_update(before, after):
    await log_member_update(before, after)


@bot.event
async def on_message_delete(message):
    await log_message_delete(message)


@bot.event
async def on_message_edit(before, after):
    await log_message_edit(before, after)


@bot.event
async def on_guild_channel_create(channel):
    await log_channel_create(channel)


@bot.event
async def on_guild_channel_delete(channel):
    await log_channel_delete(channel)


@bot.event
async def on_guild_channel_update(before, after):
    await log_channel_update(before, after)


@bot.event
async def on_guild_role_create(role):
    await log_role_create(role)


@bot.event
async def on_guild_role_delete(role):
    await log_role_delete(role)


@bot.event
async def on_guild_role_update(before, after):
    await log_role_update(before, after)


@bot.event
async def on_voice_state_update(member, before, after):
    await log_voice_state_update(member, before, after)


@bot.event
async def on_member_ban(guild, user):
    await log_member_ban(guild, user)


@bot.event
async def on_member_unban(guild, user):
    await log_member_unban(guild, user)


@bot.event
async def on_guild_emojis_update(guild, before, after):
    await log_emojis_update(guild, before, after)


@bot.event
async def on_guild_join(guild):
    await log_guild_join(guild)
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{len(bot.guilds)} sunucu | NEXOS Galaksiyi İzliyor"
        )
    )


@bot.event
async def on_guild_remove(guild):
    await log_guild_remove(guild)
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{len(bot.guilds)} sunucu | NEXOS Galaksiyi İzliyor"
        )
    )


@bot.event
async def on_interaction(interaction):
    await log_interaction(interaction)


@bot.tree.error
async def on_app_command_error(interaction, error):
    await handle_app_command_error(interaction, error)


if not DISCORD_TOKEN:
    raise RuntimeError("DISCORD_TOKEN ortam degiskeni eksik. Render Environment alanina ekle.")

bot.run(DISCORD_TOKEN)
