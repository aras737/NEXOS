from discord import app_commands

from core.embeds import make_embed
from core.emojis import with_emoji
from core.logging import log_event
from core.music import (
    MusicError,
    leave_music,
    now_playing_embed,
    pause_music,
    play_music,
    resume_music,
    skip_music,
    stop_music
)


async def send_music_error(interaction, error):
    embed = make_embed(with_emoji("music", "Muzik Hata"), str(error), 0xE74C3C)
    if interaction.response.is_done():
        await interaction.followup.send(embed=embed, ephemeral=True)
    else:
        await interaction.response.send_message(embed=embed, ephemeral=True)

    await log_event(
        interaction.guild,
        with_emoji("music", "Muzik Komut Hata"),
        str(error),
        0xE74C3C,
        [("Yetkili", f"{interaction.user} ({interaction.user.id})")],
        log_type="voice"
    )


def register(bot):
    @bot.tree.command(name="music-play", description="Ses kanalinda muzik acar veya siraya ekler.")
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.bot_has_permissions(connect=True, speak=True, embed_links=True)
    @app_commands.describe(query="YouTube linki veya arama metni.")
    async def music_play(interaction, query: app_commands.Range[str, 2, 300]):
        await interaction.response.defer(thinking=True)
        try:
            embed = await play_music(interaction, str(query))
        except MusicError as error:
            await send_music_error(interaction, error)
            return
        await interaction.followup.send(embed=embed)

    @bot.tree.command(name="music-skip", description="Calan muzigi atlar.")
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.bot_has_permissions(connect=True, speak=True, embed_links=True)
    async def music_skip(interaction):
        try:
            embed = await skip_music(interaction)
        except MusicError as error:
            await send_music_error(interaction, error)
            return
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="music-stop", description="Muzigi durdurur ve sirayi temizler.")
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.bot_has_permissions(connect=True, speak=True, embed_links=True)
    async def music_stop(interaction):
        try:
            embed = await stop_music(interaction)
        except MusicError as error:
            await send_music_error(interaction, error)
            return
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="music-pause", description="Muzigi duraklatir.")
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.bot_has_permissions(connect=True, speak=True, embed_links=True)
    async def music_pause(interaction):
        try:
            embed = await pause_music(interaction)
        except MusicError as error:
            await send_music_error(interaction, error)
            return
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="music-resume", description="Duraklatilan muzigi devam ettirir.")
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.bot_has_permissions(connect=True, speak=True, embed_links=True)
    async def music_resume(interaction):
        try:
            embed = await resume_music(interaction)
        except MusicError as error:
            await send_music_error(interaction, error)
            return
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="music-leave", description="Botu ses kanalindan cikarir.")
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.bot_has_permissions(connect=True, speak=True, embed_links=True)
    async def music_leave(interaction):
        try:
            embed = await leave_music(interaction)
        except MusicError as error:
            await send_music_error(interaction, error)
            return
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="music-now", description="Calan muzigi ve sira sayisini gosterir.")
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def music_now(interaction):
        await interaction.response.send_message(embed=now_playing_embed(interaction.guild), ephemeral=True)
