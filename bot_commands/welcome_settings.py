import discord
from discord import app_commands

from core.embeds import make_embed
from core.logging import log_event
from core.storage import get_guild_setting, set_guild_setting
from core.welcome import DEFAULT_LEAVE_MESSAGE, DEFAULT_WELCOME_MESSAGE


def channel_text(channel_id, guild):
    if not channel_id:
        return "Ayarlanmadi"
    channel = guild.get_channel(int(channel_id))
    return channel.mention if channel else str(channel_id)


def register(bot):
    @bot.tree.command(name="welcome-settings", description="Giris-cikis log ve galaksi hos geldin mesajlarini ayarlar.")
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.bot_has_permissions(send_messages=True, embed_links=True)
    @app_commands.describe(
        welcome_channel="Hos geldin mesajlarinin gidecegi kanal.",
        leave_channel="Cikis mesajlarinin gidecegi kanal.",
        welcome_message="Hos geldin metni. Kullan: {mention}, {user}, {name}, {server}, {count}",
        leave_message="Cikis metni. Kullan: {user}, {name}, {server}, {count}",
        enabled="Giris-cikis mesajlarini ac/kapat."
    )
    async def welcome_settings(
        interaction,
        welcome_channel: discord.TextChannel | None = None,
        leave_channel: discord.TextChannel | None = None,
        welcome_message: app_commands.Range[str, 1, 800] | None = None,
        leave_message: app_commands.Range[str, 1, 800] | None = None,
        enabled: bool | None = None
    ):
        changed = []
        if welcome_channel:
            set_guild_setting(interaction.guild.id, "welcome_channel_id", welcome_channel.id)
            changed.append(("Hos Geldin Kanali", welcome_channel.mention))
        if leave_channel:
            set_guild_setting(interaction.guild.id, "leave_channel_id", leave_channel.id)
            changed.append(("Cikis Kanali", leave_channel.mention))
        if welcome_message:
            set_guild_setting(interaction.guild.id, "welcome_message", str(welcome_message))
            changed.append(("Hos Geldin Mesaji", str(welcome_message)))
        if leave_message:
            set_guild_setting(interaction.guild.id, "leave_message", str(leave_message))
            changed.append(("Cikis Mesaji", str(leave_message)))
        if enabled is not None:
            set_guild_setting(interaction.guild.id, "welcome_enabled", bool(enabled))
            changed.append(("Durum", "Acik" if enabled else "Kapali"))

        welcome_channel_id = get_guild_setting(interaction.guild.id, "welcome_channel_id")
        leave_channel_id = get_guild_setting(interaction.guild.id, "leave_channel_id")
        current_welcome = get_guild_setting(interaction.guild.id, "welcome_message", DEFAULT_WELCOME_MESSAGE)
        current_leave = get_guild_setting(interaction.guild.id, "leave_message", DEFAULT_LEAVE_MESSAGE)
        current_enabled = get_guild_setting(interaction.guild.id, "welcome_enabled", True)

        embed = make_embed(
            "Giris-Cikis Ayarlari",
            "NEXOS galaksi hos geldin ve cikis sistemi guncellendi." if changed else "Mevcut giris-cikis ayarlari.",
            0x8B5CF6
        )
        embed.add_field(name="Durum", value="Acik" if current_enabled else "Kapali", inline=True)
        embed.add_field(name="Hos Geldin Kanali", value=channel_text(welcome_channel_id, interaction.guild), inline=True)
        embed.add_field(name="Cikis Kanali", value=channel_text(leave_channel_id, interaction.guild), inline=True)
        embed.add_field(name="Hos Geldin Mesaji", value=current_welcome[:1024], inline=False)
        embed.add_field(name="Cikis Mesaji", value=current_leave[:1024], inline=False)
        embed.set_footer(text="Degiskenler: {mention}, {user}, {name}, {server}, {count}")

        await interaction.response.send_message(embed=embed, ephemeral=True)
        if changed:
            await log_event(
                interaction.guild,
                "Giris-Cikis Ayarlari",
                "Giris-cikis mesaj ayarlari guncellendi.",
                0x8B5CF6,
                [("Yetkili", f"{interaction.user} ({interaction.user.id})"), *changed]
            )
