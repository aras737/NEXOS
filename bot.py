import datetime
import json
import os
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands


def run_dummy_server():
    class MyHandler(SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"NEXOS Bot 7/24 Aktif!")

    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), MyHandler)
    server.serve_forever()


threading.Thread(target=run_dummy_server, daemon=True).start()

DATA_DIR = Path("data")
WARNINGS_FILE = DATA_DIR / "warnings.json"
GUILD_ID = int(os.environ.get("GUILD_ID", "0") or 0)
VOICE_CHANNEL_ID = int(os.environ.get("VOICE_CHANNEL_ID", "0") or 0)

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.voice_states = True


class NexosBot(commands.Bot):
    async def setup_hook(self):
        if GUILD_ID:
            guild = discord.Object(id=GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            print(f"{len(synced)} slash komut GUILD_ID sunucusuna yüklendi.")
        else:
            synced = await self.tree.sync()
            print(f"{len(synced)} global slash komut yüklendi.")


bot = NexosBot(command_prefix="!", intents=intents, help_command=None)


def load_warnings():
    if not WARNINGS_FILE.exists():
        return {}
    with WARNINGS_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_warnings(data):
    DATA_DIR.mkdir(exist_ok=True)
    with WARNINGS_FILE.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def add_warning(guild_id, user_id, warning):
    data = load_warnings()
    guild_key = str(guild_id)
    user_key = str(user_id)
    data.setdefault(guild_key, {})
    data[guild_key].setdefault(user_key, [])
    data[guild_key][user_key].append(warning)
    save_warnings(data)
    return data[guild_key][user_key]


def get_warnings(guild_id, user_id):
    data = load_warnings()
    return data.get(str(guild_id), {}).get(str(user_id), [])


def clear_user_warnings(guild_id, user_id):
    data = load_warnings()
    guild_key = str(guild_id)
    user_key = str(user_id)
    if guild_key in data and user_key in data[guild_key]:
        data[guild_key][user_key] = []
        save_warnings(data)


def make_embed(title, description, color=0x5865F2):
    return discord.Embed(title=title, description=description, color=color)


async def send_error(interaction, message):
    await interaction.response.send_message(
        embed=make_embed("Hata", message, 0xE74C3C),
        ephemeral=True
    )


def can_moderate(interaction, member):
    guild = interaction.guild
    moderator = interaction.user
    bot_member = guild.me

    if member == guild.owner:
        return "Sunucu sahibine işlem yapamam."
    if member.top_role >= moderator.top_role and moderator != guild.owner:
        return "Bu üye senin rolünle aynı seviyede veya daha yukarıda."
    if bot_member and member.top_role >= bot_member.top_role:
        return "Bu üye bot rolünden daha yukarıda."
    return None


@bot.event
async def on_ready():
    print(f"{bot.user} aktif. NEXOS slash moderasyon sistemi hazır.")
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="NEXOS moderasyon sistemini"
        )
    )

    if not VOICE_CHANNEL_ID:
        return

    try:
        channel = bot.get_channel(VOICE_CHANNEL_ID)
        if channel and isinstance(channel, discord.VoiceChannel):
            if not discord.utils.get(bot.voice_clients, guild=channel.guild):
                await channel.connect()
            print(f"Ses kanalına bağlandı: {channel.name}")
        else:
            print("VOICE_CHANNEL_ID geçerli bir ses kanalı değil.")
    except Exception as error:
        print(f"Ses kanalına bağlanırken hata oluştu: {error}")


@bot.event
async def on_member_join(member):
    channel = member.guild.system_channel
    if not channel:
        return

    embed = discord.Embed(
        title="NEXOS'a Hoş Geldin",
        description=f"Hoş geldin {member.mention}! Sunucuya iniş yaptın.",
        color=0x9B5DE5
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    await channel.send(embed=embed)


@bot.tree.error
async def on_app_command_error(interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        message = "Bu komut için yetkin yok."
    elif isinstance(error, app_commands.BotMissingPermissions):
        message = "Bu işlem için botun gerekli izni yok."
    else:
        print(error)
        message = "Komut çalışırken hata oluştu. Bot izinlerini ve rol sırasını kontrol et."

    if interaction.response.is_done():
        await interaction.followup.send(embed=make_embed("Hata", message, 0xE74C3C), ephemeral=True)
    else:
        await interaction.response.send_message(embed=make_embed("Hata", message, 0xE74C3C), ephemeral=True)


@bot.tree.command(name="help", description="Komut listesini gösterir.")
@app_commands.guild_only()
async def help_command(interaction):
    commands_text = [
        "`/help` komut listesini gösterir.",
        "`/ping` bot gecikmesini gösterir.",
        "`/server` sunucu bilgilerini gösterir.",
        "`/user` üye bilgilerini gösterir.",
        "`/clear` mesaj siler.",
        "`/kick` üyeyi atar.",
        "`/ban` üyeyi banlar.",
        "`/unban` ban kaldırır.",
        "`/timeout` üyeyi susturur.",
        "`/untimeout` susturmayı kaldırır.",
        "`/warn` uyarı verir.",
        "`/warnings` uyarıları listeler.",
        "`/clear-warnings` uyarıları temizler.",
        "`/role-add` rol verir.",
        "`/role-remove` rol alır.",
        "`/lock` kanalı kilitler.",
        "`/unlock` kanal kilidini açar.",
        "`/slowmode` yavaş modu ayarlar.",
        "`/say` bot adına mesaj gönderir.",
        "`/embed` embed mesaj gönderir.",
        "`/kurulum` temel kanal kurulumunu yapar."
    ]
    await interaction.response.send_message(
        embed=make_embed("NEXOS Slash Komutları", "\n".join(commands_text)),
        ephemeral=True
    )


@bot.tree.command(name="ping", description="Bot gecikmesini gösterir.")
@app_commands.guild_only()
async def ping(interaction):
    await interaction.response.send_message(f"Pong! {round(bot.latency * 1000)}ms", ephemeral=True)


@bot.tree.command(name="server", description="Sunucu bilgilerini gösterir.")
@app_commands.guild_only()
async def server(interaction):
    guild = interaction.guild
    embed = make_embed(guild.name, "Sunucu bilgileri", 0x3498DB)
    embed.add_field(name="Üyeler", value=str(guild.member_count), inline=True)
    embed.add_field(name="Kanallar", value=str(len(guild.channels)), inline=True)
    embed.add_field(name="Roller", value=str(len(guild.roles)), inline=True)
    embed.add_field(name="Oluşturma", value=discord.utils.format_dt(guild.created_at, "D"), inline=True)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="user", description="Üye bilgilerini gösterir.")
@app_commands.guild_only()
async def user(interaction, member: discord.Member | None = None):
    member = member or interaction.user
    embed = make_embed(str(member), "Üye bilgileri", 0x3498DB)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="ID", value=str(member.id), inline=True)
    embed.add_field(name="Hesap", value=discord.utils.format_dt(member.created_at, "D"), inline=True)
    embed.add_field(name="Katılım", value=discord.utils.format_dt(member.joined_at, "D"), inline=True)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="clear", description="Kanaldan mesaj siler.")
@app_commands.guild_only()
@app_commands.default_permissions(manage_messages=True)
@app_commands.checks.bot_has_permissions(manage_messages=True)
async def clear(interaction, amount: app_commands.Range[int, 1, 100]):
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.response.send_message(
        embed=make_embed("Mesajlar silindi", f"{len(deleted)} mesaj silindi.", 0x2ECC71),
        ephemeral=True
    )


@bot.tree.command(name="kick", description="Üyeyi sunucudan atar.")
@app_commands.guild_only()
@app_commands.default_permissions(kick_members=True)
@app_commands.checks.bot_has_permissions(kick_members=True)
async def kick(interaction, member: discord.Member, reason: str = "Sebep belirtilmedi"):
    issue = can_moderate(interaction, member)
    if issue:
        return await send_error(interaction, issue)

    await member.kick(reason=reason)
    await interaction.response.send_message(
        embed=make_embed("Üye atıldı", f"{member.mention} sunucudan atıldı.\nSebep: {reason}", 0x2ECC71)
    )


@bot.tree.command(name="ban", description="Üyeyi banlar.")
@app_commands.guild_only()
@app_commands.default_permissions(ban_members=True)
@app_commands.checks.bot_has_permissions(ban_members=True)
async def ban(interaction, member: discord.Member, reason: str = "Sebep belirtilmedi"):
    issue = can_moderate(interaction, member)
    if issue:
        return await send_error(interaction, issue)

    await member.ban(reason=reason, delete_message_days=0)
    await interaction.response.send_message(
        embed=make_embed("Üye banlandı", f"{member} banlandı.\nSebep: {reason}", 0x2ECC71)
    )


@bot.tree.command(name="unban", description="ID ile ban kaldırır.")
@app_commands.guild_only()
@app_commands.default_permissions(ban_members=True)
@app_commands.checks.bot_has_permissions(ban_members=True)
async def unban(interaction, user_id: str, reason: str = "Sebep belirtilmedi"):
    user = await bot.fetch_user(int(user_id))
    await interaction.guild.unban(user, reason=reason)
    await interaction.response.send_message(embed=make_embed("Ban kaldırıldı", f"{user} banı kaldırıldı.", 0x2ECC71))


@bot.tree.command(name="timeout", description="Üyeyi geçici susturur.")
@app_commands.guild_only()
@app_commands.default_permissions(moderate_members=True)
@app_commands.checks.bot_has_permissions(moderate_members=True)
async def timeout(
    interaction,
    member: discord.Member,
    minutes: app_commands.Range[int, 1, 40320],
    reason: str = "Sebep belirtilmedi"
):
    issue = can_moderate(interaction, member)
    if issue:
        return await send_error(interaction, issue)

    await member.timeout(datetime.timedelta(minutes=minutes), reason=reason)
    await interaction.response.send_message(
        embed=make_embed("Üye susturuldu", f"{member.mention} {minutes} dakika susturuldu.", 0x2ECC71)
    )


@bot.tree.command(name="untimeout", description="Üyenin susturmasını kaldırır.")
@app_commands.guild_only()
@app_commands.default_permissions(moderate_members=True)
@app_commands.checks.bot_has_permissions(moderate_members=True)
async def untimeout(interaction, member: discord.Member, reason: str = "Sebep belirtilmedi"):
    await member.timeout(None, reason=reason)
    await interaction.response.send_message(
        embed=make_embed("Susturma kaldırıldı", f"{member.mention} susturması kaldırıldı.", 0x2ECC71)
    )


@bot.tree.command(name="warn", description="Üyeye uyarı verir.")
@app_commands.guild_only()
@app_commands.default_permissions(moderate_members=True)
async def warn(interaction, member: discord.Member, reason: str):
    warnings = add_warning(
        interaction.guild.id,
        member.id,
        {
            "reason": reason,
            "moderator_id": interaction.user.id,
            "created_at": datetime.datetime.utcnow().isoformat()
        }
    )
    await interaction.response.send_message(
        embed=make_embed("Uyarı verildi", f"{member.mention} uyarıldı. Toplam uyarı: {len(warnings)}", 0xF1C40F)
    )


@bot.tree.command(name="warnings", description="Üyenin uyarılarını listeler.")
@app_commands.guild_only()
@app_commands.default_permissions(moderate_members=True)
async def warnings_command(interaction, member: discord.Member):
    warnings = get_warnings(interaction.guild.id, member.id)
    if not warnings:
        description = "Uyarı yok."
    else:
        description = "\n".join(
            f"{index + 1}. {item['reason']} - <@{item['moderator_id']}>"
            for index, item in enumerate(warnings)
        )
    await interaction.response.send_message(
        embed=make_embed(f"{member} uyarıları", description, 0xF1C40F),
        ephemeral=True
    )


@bot.tree.command(name="clear-warnings", description="Üyenin uyarılarını temizler.")
@app_commands.guild_only()
@app_commands.default_permissions(moderate_members=True)
async def clear_warnings_command(interaction, member: discord.Member):
    clear_user_warnings(interaction.guild.id, member.id)
    await interaction.response.send_message(
        embed=make_embed("Uyarılar temizlendi", f"{member.mention} uyarıları temizlendi.", 0x2ECC71),
        ephemeral=True
    )


@bot.tree.command(name="role-add", description="Üyeye rol verir.")
@app_commands.guild_only()
@app_commands.default_permissions(manage_roles=True)
@app_commands.checks.bot_has_permissions(manage_roles=True)
async def role_add(interaction, member: discord.Member, role: discord.Role):
    await member.add_roles(role, reason=f"{interaction.user} tarafından rol verildi")
    await interaction.response.send_message(
        embed=make_embed("Rol verildi", f"{member.mention} üyesine {role.mention} rolü verildi.", 0x2ECC71)
    )


@bot.tree.command(name="role-remove", description="Üyeden rol alır.")
@app_commands.guild_only()
@app_commands.default_permissions(manage_roles=True)
@app_commands.checks.bot_has_permissions(manage_roles=True)
async def role_remove(interaction, member: discord.Member, role: discord.Role):
    await member.remove_roles(role, reason=f"{interaction.user} tarafından rol alındı")
    await interaction.response.send_message(
        embed=make_embed("Rol alındı", f"{member.mention} üyesinden {role.mention} rolü alındı.", 0x2ECC71)
    )


@bot.tree.command(name="lock", description="Bulunduğun kanalı kilitler.")
@app_commands.guild_only()
@app_commands.default_permissions(manage_channels=True)
@app_commands.checks.bot_has_permissions(manage_channels=True)
async def lock(interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
    await interaction.response.send_message(embed=make_embed("Kanal kilitlendi", "Bu kanalda mesaj gönderme kapatıldı.", 0x2ECC71))


@bot.tree.command(name="unlock", description="Bulunduğun kanalın kilidini açar.")
@app_commands.guild_only()
@app_commands.default_permissions(manage_channels=True)
@app_commands.checks.bot_has_permissions(manage_channels=True)
async def unlock(interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=None)
    await interaction.response.send_message(embed=make_embed("Kanal açıldı", "Bu kanalda mesaj gönderme izni normale döndü.", 0x2ECC71))


@bot.tree.command(name="slowmode", description="Kanal yavaş modunu ayarlar.")
@app_commands.guild_only()
@app_commands.default_permissions(manage_channels=True)
@app_commands.checks.bot_has_permissions(manage_channels=True)
async def slowmode(interaction, seconds: app_commands.Range[int, 0, 21600]):
    await interaction.channel.edit(slowmode_delay=seconds)
    await interaction.response.send_message(embed=make_embed("Yavaş mod ayarlandı", f"Yavaş mod: {seconds} saniye.", 0x2ECC71))


@bot.tree.command(name="say", description="Bot adına mesaj gönderir.")
@app_commands.guild_only()
@app_commands.default_permissions(manage_messages=True)
async def say(interaction, message: str):
    await interaction.channel.send(message)
    await interaction.response.send_message("Gönderildi.", ephemeral=True)


@bot.tree.command(name="embed", description="Embed mesaj gönderir.")
@app_commands.guild_only()
@app_commands.default_permissions(manage_messages=True)
async def embed(interaction, title: str, description: str):
    await interaction.channel.send(embed=make_embed(title, description))
    await interaction.response.send_message("Gönderildi.", ephemeral=True)


@bot.tree.command(name="kurulum", description="Temel sunucu kanal kurulumunu yapar.")
@app_commands.guild_only()
@app_commands.default_permissions(administrator=True)
async def kurulum(interaction):
    guild = interaction.guild
    await interaction.response.defer(thinking=True, ephemeral=True)

    try:
        info_category = await guild.create_category("BİLGİ MERKEZİ")
        await guild.create_text_channel("kurallar", category=info_category)
        await guild.create_text_channel("duyurular", category=info_category)
        await guild.create_text_channel("rol-al", category=info_category)

        lobby_category = await guild.create_category("SOHBET")
        await guild.create_text_channel("genel-sohbet", category=lobby_category)
        await guild.create_text_channel("bot-komut", category=lobby_category)
        await guild.create_text_channel("medya", category=lobby_category)

        voice_category = await guild.create_category("SES KANALLARI")
        await guild.create_voice_channel("Genel Ses", category=voice_category)
        await guild.create_voice_channel("Duo #1", category=voice_category, user_limit=2)
        await guild.create_voice_channel("Squad #1", category=voice_category, user_limit=5)
        await guild.create_voice_channel("AFK", category=voice_category)

        await interaction.followup.send("NEXOS kurulumu başarıyla tamamlandı.", ephemeral=True)
    except Exception as error:
        await interaction.followup.send(f"Hata: {error}", ephemeral=True)


token = os.getenv("DISCORD_TOKEN")
if not token:
    raise RuntimeError("DISCORD_TOKEN ortam değişkeni eksik.")

bot.run(token)
