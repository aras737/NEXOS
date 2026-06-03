import discord
from discord.ext import commands
import os
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer

# --- 🌐 RENDER İÇİN MİNİ WEB SUNUCUSU ---
def run_dummy_server():
    class MyHandler(SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"NEXON Bot 7/24 Aktif!")

    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), MyHandler)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()


# --- 🪐 BOT AYARLARI ---
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.voice_states = True  # Sese bağlanabilmesi için bu izni de ekledik kanka

bot = commands.Bot(command_prefix="!", intents=intents)

# ⚠️ BURAYA AZ ÖNCE KOPYALADIĞIN SES KANALININ ID'SİNİ YAZ (Tırnak işaretleri olmadan, sadece sayı)
SES_KANAL_ID = 1511798754980663488 

@bot.event
async def on_ready():
    print(f"🪐 {bot.user} galaksiye iniş yaptı! NEXON sistemi aktif.")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="NEXON Uzayını"))

    # --- 🔊 OTOMATİK SESE BAĞLANMA KISMI ---
    try:
        channel = bot.get_channel(SES_KANAL_ID)
        if channel and isinstance(channel, discord.VoiceChannel):
            # Eğer bot zaten o odada değilse bağlanmasını söylüyoruz
            await channel.connect()
            print(f"🔊 Başarıyla '{channel.name}' ses kanalına giriş yapıldı!")
        else:
            print("❌ Belirttiğin ses kanalı bulunamadı veya bir ses kanalı değil!")
    except Exception as e:
        print(f"❌ Ses kanalına bağlanırken hata oluştu: {e}")


@bot.event
async def on_member_join(member):
    channel = member.guild.system_channel
    if channel:
        embed = discord.Embed(
            title="🌌 Yeni Bir Gezgin Yaklaşıyor!",
            description=f"Hoş geldin {member.mention}! **NEXON** derin uzay topluluğuna iniş yaptın.",
            color=0x9b5de5
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await channel.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def kurulum(ctx):
    guild = ctx.guild
    await ctx.send("🔮 **NEXON Kozmik Altyapı Kurulumu Başlatılıyor...**")
    try:
        kat_bilgi = await guild.create_category("🛰️ ︱ BİLGİ MERKEZİ")
        await guild.create_text_channel("📌 ︱ kurallar", category=kat_bilgi)
        await guild.create_text_channel("📢 ︱ duyurular", category=kat_bilgi)
        await guild.create_text_channel("🎭 ︱ rol-al", category=kat_bilgi)

        kat_lobi = await guild.create_category("🌌 ︱ KOZMİK LOBİ")
        await guild.create_text_channel("💬 ︱ kara-delik-sohbet", category=kat_lobi)
        await guild.create_text_channel("🤖 ︱ bot-komut", category=kat_lobi)
        await guild.create_text_channel("📷 ︱ medya", category=kat_lobi)

        kat_ses = await guild.create_category("🔊 ︱ SES KANALLARI")
        await guild.create_voice_channel("🪐 ︱ Kozmik Oda", category=kat_ses)
        await guild.create_voice_channel("⚔️ ︱ Duo #1 (2 Kişilik)", category=kat_ses, user_limit=2)
        await guild.create_voice_channel("🛡️ ︱ Squad #1 (5 Kişilik)", category=kat_ses, user_limit=5)
        await guild.create_voice_channel("💤 ︱ Sonsuz Döngü (AFK)", category=kat_ses)

        await ctx.send("✅ **Kozmik kurulum başarıyla tamamlandı!**")
    except Exception as e:
        await ctx.send(f"❌ Hata: {e}")

bot.run(os.getenv('DISCORD_TOKEN'))
