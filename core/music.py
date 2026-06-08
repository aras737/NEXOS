import asyncio
import shutil

import discord

from core.embeds import make_embed
from core.emojis import with_emoji
from core.logging import log_event, trim


YTDL_OPTIONS = {
    "format": "bestaudio/best",
    "default_search": "ytsearch",
    "noplaylist": True,
    "quiet": True,
    "no_warnings": True,
    "ignoreerrors": False,
    "nocheckcertificate": True,
    "source_address": "0.0.0.0"
}

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn"
}

MAX_QUEUE_SIZE = 20
MUSIC_STATES = {}


class MusicError(Exception):
    pass


class GuildMusicState:
    def __init__(self):
        self.queue = []
        self.current = None
        self.text_channel_id = None
        self.loop = None


def get_music_state(guild_id):
    state = MUSIC_STATES.get(int(guild_id))
    if not state:
        state = GuildMusicState()
        MUSIC_STATES[int(guild_id)] = state
    return state


def duration_text(seconds):
    if not seconds:
        return "Bilinmiyor"
    seconds = int(seconds)
    minutes, second = divmod(seconds, 60)
    hour, minute = divmod(minutes, 60)
    if hour:
        return f"{hour}:{minute:02d}:{second:02d}"
    return f"{minute}:{second:02d}"


def require_ffmpeg():
    if ffmpeg_executable():
        return
    raise MusicError("Render/ortam icinde `ffmpeg` bulunamadi. Muzik icin ffmpeg gerekli.")


def ffmpeg_executable():
    executable = shutil.which("ffmpeg")
    if executable:
        return executable
    try:
        import imageio_ffmpeg
    except ModuleNotFoundError:
        return None
    return imageio_ffmpeg.get_ffmpeg_exe()


def voice_channel_for(member):
    voice_state = getattr(member, "voice", None)
    channel = getattr(voice_state, "channel", None)
    if not channel:
        raise MusicError("Once bir ses kanalina girmen lazim.")
    return channel


async def ensure_voice_client(interaction):
    channel = voice_channel_for(interaction.user)
    voice_client = interaction.guild.voice_client

    if voice_client and voice_client.is_connected():
        if voice_client.channel != channel:
            await voice_client.move_to(channel)
        return voice_client

    return await channel.connect()


async def extract_track(query, requester):
    try:
        import yt_dlp
    except ModuleNotFoundError as error:
        raise MusicError("`yt-dlp` paketi kurulu degil. Render yeniden deploy edilince requirements ile kurulur.") from error

    search_query = query if query.startswith(("http://", "https://")) else f"ytsearch1:{query}"

    def extract():
        with yt_dlp.YoutubeDL(YTDL_OPTIONS) as ytdl:
            return ytdl.extract_info(search_query, download=False)

    info = await asyncio.to_thread(extract)
    if not info:
        raise MusicError("Sarki bulunamadi.")

    if info.get("entries"):
        entries = [entry for entry in info["entries"] if entry]
        if not entries:
            raise MusicError("Sarki bulunamadi.")
        info = entries[0]

    stream_url = info.get("url")
    if not stream_url:
        raise MusicError("Ses kaynagi alinamadi.")

    return {
        "title": info.get("title") or query,
        "stream_url": stream_url,
        "webpage_url": info.get("webpage_url") or info.get("original_url") or query,
        "duration": int(info.get("duration") or 0),
        "requester_id": requester.id,
        "requester_name": str(requester)
    }


def track_line(track):
    title = trim(track.get("title", "Bilinmeyen"), 80)
    url = track.get("webpage_url") or ""
    duration = duration_text(track.get("duration"))
    return f"[{title}]({url}) • {duration}" if url.startswith(("http://", "https://")) else f"{title} • {duration}"


async def announce_next(guild, track):
    state = get_music_state(guild.id)
    channel = guild.get_channel(state.text_channel_id) if state.text_channel_id else None
    if not channel:
        return
    try:
        await channel.send(
            embed=make_embed(
                with_emoji("music", "Muzik Basladi"),
                track_line(track),
                0x22C55E
            )
        )
    except discord.HTTPException:
        pass


async def handle_track_finished(guild, track, error):
    state = get_music_state(guild.id)
    if error:
        await log_event(
            guild,
            with_emoji("music", "Muzik Hata"),
            f"`{track.get('title', 'Bilinmeyen')}` calarken hata olustu.",
            0xE74C3C,
            [("Hata", trim(error, 1000))],
            log_type="voice"
        )
    state.current = None
    await play_next(guild)


async def play_next(guild):
    state = get_music_state(guild.id)
    voice_client = guild.voice_client
    if not voice_client or not voice_client.is_connected():
        state.current = None
        return
    if voice_client.is_playing() or voice_client.is_paused():
        return
    if not state.queue:
        state.current = None
        return

    track = state.queue.pop(0)
    state.current = track
    source = discord.FFmpegPCMAudio(track["stream_url"], executable=ffmpeg_executable(), **FFMPEG_OPTIONS)

    def after(error):
        if state.loop:
            state.loop.call_soon_threadsafe(
                asyncio.create_task,
                handle_track_finished(guild, track, error)
            )

    try:
        voice_client.play(source, after=after)
    except Exception as error:
        state.current = None
        await log_event(
            guild,
            with_emoji("music", "Muzik Baslatilamadi"),
            f"`{track.get('title', 'Bilinmeyen')}` baslatilamadi.",
            0xE74C3C,
            [("Hata", trim(error, 1000))],
            log_type="voice"
        )
        await play_next(guild)
        return

    await announce_next(guild, track)
    await log_event(
        guild,
        with_emoji("music", "Muzik Basladi"),
        track_line(track),
        0x22C55E,
        [
            ("Isteyen", f"{track['requester_name']} ({track['requester_id']})"),
            ("Kalan Sira", str(len(state.queue)))
        ],
        log_type="voice"
    )


async def play_music(interaction, query):
    require_ffmpeg()
    voice_client = await ensure_voice_client(interaction)
    state = get_music_state(interaction.guild.id)
    state.text_channel_id = interaction.channel_id
    state.loop = interaction.client.loop

    if len(state.queue) >= MAX_QUEUE_SIZE:
        raise MusicError(f"Sira dolu. Maksimum {MAX_QUEUE_SIZE} sarki bekleyebilir.")

    track = await extract_track(query, interaction.user)
    is_idle = not voice_client.is_playing() and not voice_client.is_paused() and not state.current
    state.queue.append(track)

    await log_event(
        interaction.guild,
        with_emoji("music", "Muzik Siraya Eklendi" if not is_idle else "Muzik Istendi"),
        track_line(track),
        0x3B82F6,
        [
            ("Yetkili", f"{interaction.user} ({interaction.user.id})"),
            ("Ses Kanali", f"{voice_client.channel} ({voice_client.channel.id})"),
            ("Sira", str(len(state.queue)))
        ],
        log_type="voice"
    )

    if is_idle:
        await play_next(interaction.guild)
        return make_embed(with_emoji("music", "Muzik Acildi"), track_line(track), 0x22C55E)

    return make_embed(
        with_emoji("music", "Siraya Eklendi"),
        f"{track_line(track)}\nSira konumu: **{len(state.queue)}**",
        0x3B82F6
    )


async def skip_music(interaction):
    state = get_music_state(interaction.guild.id)
    voice_client = interaction.guild.voice_client
    if not voice_client or not (voice_client.is_playing() or voice_client.is_paused()):
        raise MusicError("Su an calan muzik yok.")

    skipped = state.current
    voice_client.stop()
    await log_event(
        interaction.guild,
        with_emoji("music", "Muzik Atlandi"),
        track_line(skipped) if skipped else "Calan muzik atlandi.",
        0xF59E0B,
        [("Yetkili", f"{interaction.user} ({interaction.user.id})")],
        log_type="voice"
    )
    return make_embed(with_emoji("music", "Muzik Atlandi"), "Siradaki muzik varsa otomatik baslar.", 0xF59E0B)


async def stop_music(interaction):
    state = get_music_state(interaction.guild.id)
    voice_client = interaction.guild.voice_client
    if not voice_client:
        raise MusicError("Bot su an ses kanalinda degil.")

    state.queue.clear()
    state.current = None
    if voice_client.is_playing() or voice_client.is_paused():
        voice_client.stop()

    await log_event(
        interaction.guild,
        with_emoji("music", "Muzik Durduruldu"),
        "Muzik durduruldu ve sira temizlendi.",
        0xEF4444,
        [("Yetkili", f"{interaction.user} ({interaction.user.id})")],
        log_type="voice"
    )
    return make_embed(with_emoji("music", "Muzik Durduruldu"), "Sira temizlendi.", 0xEF4444)


async def pause_music(interaction):
    voice_client = interaction.guild.voice_client
    if not voice_client or not voice_client.is_playing():
        raise MusicError("Duraklatilacak muzik yok.")
    voice_client.pause()
    await log_event(
        interaction.guild,
        with_emoji("music", "Muzik Duraklatildi"),
        f"{interaction.user.mention} muzigi duraklatti.",
        0xF59E0B,
        log_type="voice"
    )
    return make_embed(with_emoji("music", "Duraklatildi"), "Muzik duraklatildi.", 0xF59E0B)


async def resume_music(interaction):
    voice_client = interaction.guild.voice_client
    if not voice_client or not voice_client.is_paused():
        raise MusicError("Devam ettirilecek duraklatilmis muzik yok.")
    voice_client.resume()
    await log_event(
        interaction.guild,
        with_emoji("music", "Muzik Devam"),
        f"{interaction.user.mention} muzigi devam ettirdi.",
        0x22C55E,
        log_type="voice"
    )
    return make_embed(with_emoji("music", "Devam"), "Muzik devam ediyor.", 0x22C55E)


async def leave_music(interaction):
    state = get_music_state(interaction.guild.id)
    voice_client = interaction.guild.voice_client
    if not voice_client:
        raise MusicError("Bot su an ses kanalinda degil.")

    channel = voice_client.channel
    state.queue.clear()
    state.current = None
    await voice_client.disconnect(force=True)
    await log_event(
        interaction.guild,
        with_emoji("music", "Muzik Ses Kanalindan Ayrildi"),
        f"Bot {channel} kanalindan ayrildi.",
        0x64748B,
        [("Yetkili", f"{interaction.user} ({interaction.user.id})")],
        log_type="voice"
    )
    return make_embed(with_emoji("music", "Ayrildi"), "Bot ses kanalindan ayrildi.", 0x64748B)


def now_playing_embed(guild):
    state = get_music_state(guild.id)
    if not state.current:
        return make_embed(with_emoji("music", "Muzik Yok"), "Su an calan muzik yok.", 0x64748B)

    embed = make_embed(with_emoji("music", "Su An Caliyor"), track_line(state.current), 0x22C55E)
    embed.add_field(name="Sira", value=str(len(state.queue)), inline=True)
    embed.add_field(name="Isteyen", value=f"<@{state.current['requester_id']}>", inline=True)
    return embed
