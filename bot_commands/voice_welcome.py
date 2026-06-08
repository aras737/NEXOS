import discord
from discord import app_commands

from core.emojis import with_emoji
from core.logging import log_event
from core.storage import get_guild_setting, set_guild_setting
from core.voice_welcome import voice_welcome_settings_embed


def update_role_list(guild_id, key, role, clear):
    if clear:
        set_guild_setting(guild_id, key, [])
        return "Temizlendi"
    if not role:
        return None

    role_ids = get_guild_setting(guild_id, key, [])
    if not isinstance(role_ids, list):
        role_ids = []
    if role.id not in [int(item) for item in role_ids]:
        role_ids.append(role.id)
    set_guild_setting(guild_id, key, role_ids)
    return role.mention


def register(bot):
    @bot.tree.command(name="voice-welcome-settings", description="Ses kanalina girislerde calacak welcome sesini ayarlar.")
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.bot_has_permissions(connect=True, speak=True, embed_links=True)
    @app_commands.describe(
        channel="Voice welcome icin dinlenecek ses kanali.",
        welcome_sound="Kayitsiz/normal uye girince calacak mp3/wav URL veya Render dosya yolu.",
        staff_sound="Yetkili ve kayitsiz ayni kanalda ilk kez bulusunca calacak ses.",
        staff_role="Yetkili sayilacak rol. Tekrar kullanarak yeni rol eklenir.",
        unregistered_role="Kayitsiz sayilacak rol. Bos birakilirsa bot olmayan herkes sayilir.",
        clear_staff_roles="Yetkili rol listesini temizler.",
        clear_unregistered_roles="Kayitsiz rol listesini temizler.",
        enabled="Voice welcome sistemini ac/kapat."
    )
    async def voice_welcome_settings(
        interaction,
        channel: discord.VoiceChannel | None = None,
        welcome_sound: app_commands.Range[str, 1, 500] | None = None,
        staff_sound: app_commands.Range[str, 1, 500] | None = None,
        staff_role: discord.Role | None = None,
        unregistered_role: discord.Role | None = None,
        clear_staff_roles: bool | None = None,
        clear_unregistered_roles: bool | None = None,
        enabled: bool | None = None
    ):
        changed = []
        guild_id = interaction.guild.id

        if channel:
            set_guild_setting(guild_id, "voice_welcome_channel_id", channel.id)
            changed.append(("Voice Welcome Kanali", f"{channel.mention} ({channel.id})"))
        if welcome_sound:
            set_guild_setting(guild_id, "voice_welcome_sound", str(welcome_sound))
            changed.append(("Welcome Ses", str(welcome_sound)))
        if staff_sound:
            set_guild_setting(guild_id, "voice_welcome_staff_sound", str(staff_sound))
            changed.append(("Yetkili Ses", str(staff_sound)))
        if enabled is not None:
            set_guild_setting(guild_id, "voice_welcome_enabled", bool(enabled))
            changed.append(("Durum", "Acik" if enabled else "Kapali"))

        staff_change = update_role_list(guild_id, "voice_welcome_staff_role_ids", staff_role, bool(clear_staff_roles))
        if staff_change:
            changed.append(("Yetkili Rolleri", staff_change))

        unregistered_change = update_role_list(
            guild_id,
            "voice_welcome_unregistered_role_ids",
            unregistered_role,
            bool(clear_unregistered_roles)
        )
        if unregistered_change:
            changed.append(("Kayitsiz Rolleri", unregistered_change))

        embed = voice_welcome_settings_embed(interaction.guild)
        await interaction.response.send_message(embed=embed, ephemeral=True)

        if changed:
            await log_event(
                interaction.guild,
                with_emoji("voice", "Voice Welcome Ayarlari"),
                f"{interaction.user.mention} voice welcome ayarlarini guncelledi.",
                0x8B5CF6,
                [("Yetkili", f"{interaction.user} ({interaction.user.id})"), *changed],
                log_type="voice"
            )

    @bot.tree.command(name="voice-welcome-info", description="Voice welcome ayarlarini gosterir.")
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def voice_welcome_info(interaction):
        await interaction.response.send_message(embed=voice_welcome_settings_embed(interaction.guild), ephemeral=True)
