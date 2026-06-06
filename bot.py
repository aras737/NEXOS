import discord
from discord.ext import commands

from bot_commands import register_all_commands
from core.auto_role import apply_auto_role
from core.config import DISCORD_TOKEN, GUILD_ID, VOICE_CHANNEL_ID
from core.embeds import make_embed
from core.errors import handle_app_command_error
from core.logging import log_event, log_interaction
from core.member_counter import update_member_count_channel
from core.tickets import TicketControlView, TicketPanelView
from core.web_server import start_web_server


start_web_server()

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.voice_states = True


class NexosBot(commands.Bot):
    async def setup_hook(self):
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
            name="NEXOS Galaksiyi İzliyor"
        )
    )

    for guild in bot.guilds:
        await log_event(
            guild,
            "Bot Aktif",
            "NEXOS baslatildi ve slash komut sistemi hazir.",
            0x2ECC71
        )

    if not VOICE_CHANNEL_ID:
        return

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
        "Uye Katildi",
        f"{member.mention} sunucuya katildi.",
        0x2ECC71,
        [("Uye", f"{member} ({member.id})")]
    )
    await apply_auto_role(member)

    channel = member.guild.system_channel
    if not channel:
        return

    embed = make_embed(
        "NEXOS'a Hos Geldin",
        f"Hos geldin {member.mention}! Sunucuya inis yaptin.",
        0x9B5DE5
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    await channel.send(embed=embed)


@bot.event
async def on_member_remove(member):
    try:
        await update_member_count_channel(member.guild)
    except Exception as error:
        print(f"Uye sayaci guncellenirken hata olustu: {error}")

    await log_event(
        member.guild,
        "Uye Ayrildi",
        f"{member} sunucudan ayrildi.",
        0xE67E22,
        [("Uye", f"{member} ({member.id})")]
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
