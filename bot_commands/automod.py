from discord import app_commands

from core.automod import add_banned_word, remove_banned_word
from core.embeds import make_embed
from core.emojis import with_emoji
from core.logging import log_event
from core.storage import get_guild_setting, set_guild_setting


ACTION_CHOICES = [
    app_commands.Choice(name="Sil", value="delete"),
    app_commands.Choice(name="Uyar", value="warn"),
    app_commands.Choice(name="Timeout", value="timeout")
]


def bool_text(value):
    return "Acik" if value else "Kapali"


def automod_embed(guild):
    enabled = get_guild_setting(guild.id, "automod_enabled", True)
    anti_invite = get_guild_setting(guild.id, "automod_anti_invite", True)
    anti_links = get_guild_setting(guild.id, "automod_anti_links", False)
    anti_spam = get_guild_setting(guild.id, "automod_anti_spam", True)
    anti_mass_mention = get_guild_setting(guild.id, "automod_anti_mass_mention", True)
    action = get_guild_setting(guild.id, "automod_action", "delete")
    timeout_minutes = get_guild_setting(guild.id, "automod_timeout_minutes", 10)
    spam_messages = get_guild_setting(guild.id, "automod_spam_messages", 5)
    spam_seconds = get_guild_setting(guild.id, "automod_spam_seconds", 6)
    max_mentions = get_guild_setting(guild.id, "automod_max_mentions", 6)
    words = get_guild_setting(guild.id, "automod_banned_words", [])
    if not isinstance(words, list):
        words = []

    embed = make_embed(
        with_emoji("shield", "AutoMod Ayarlari"),
        "Davet, link, spam, cok etiket ve yasak kelime korumasi.",
        0x8B5CF6
    )
    embed.add_field(name="Durum", value=bool_text(enabled), inline=True)
    embed.add_field(name="Aksiyon", value=str(action), inline=True)
    embed.add_field(name="Timeout", value=f"{timeout_minutes} dk", inline=True)
    embed.add_field(name="Davet", value=bool_text(anti_invite), inline=True)
    embed.add_field(name="Link", value=bool_text(anti_links), inline=True)
    embed.add_field(name="Spam", value=bool_text(anti_spam), inline=True)
    embed.add_field(name="Cok Etiket", value=bool_text(anti_mass_mention), inline=True)
    embed.add_field(name="Spam Limiti", value=f"{spam_messages} mesaj / {spam_seconds} sn", inline=True)
    embed.add_field(name="Etiket Limiti", value=str(max_mentions), inline=True)
    embed.add_field(name="Yasak Kelimeler", value=", ".join(words[:30]) if words else "Yok", inline=False)
    return embed


def register(bot):
    @bot.tree.command(name="automod-settings", description="AutoMod sistemini ayarlar.")
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.bot_has_permissions(manage_messages=True, embed_links=True)
    @app_commands.choices(action=ACTION_CHOICES)
    async def automod_settings(
        interaction,
        enabled: bool | None = None,
        anti_invite: bool | None = None,
        anti_links: bool | None = None,
        anti_spam: bool | None = None,
        anti_mass_mention: bool | None = None,
        action: app_commands.Choice[str] | None = None,
        timeout_minutes: app_commands.Range[int, 1, 1440] | None = None,
        spam_messages: app_commands.Range[int, 3, 20] | None = None,
        spam_seconds: app_commands.Range[int, 3, 60] | None = None,
        max_mentions: app_commands.Range[int, 3, 30] | None = None
    ):
        changed = []
        updates = {
            "enabled": enabled,
            "anti_invite": anti_invite,
            "anti_links": anti_links,
            "anti_spam": anti_spam,
            "anti_mass_mention": anti_mass_mention,
            "timeout_minutes": timeout_minutes,
            "spam_messages": spam_messages,
            "spam_seconds": spam_seconds,
            "max_mentions": max_mentions
        }
        for key, value in updates.items():
            if value is not None:
                set_guild_setting(interaction.guild.id, f"automod_{key}", value)
                changed.append((key, bool_text(value) if isinstance(value, bool) else str(value)))

        if action:
            set_guild_setting(interaction.guild.id, "automod_action", action.value)
            changed.append(("action", action.value))

        await interaction.response.send_message(embed=automod_embed(interaction.guild), ephemeral=True)
        if changed:
            await log_event(
                interaction.guild,
                with_emoji("shield", "AutoMod Ayarlari Guncellendi"),
                f"{interaction.user.mention} AutoMod ayarlarini guncelledi.",
                0x8B5CF6,
                [("Yetkili", f"{interaction.user} ({interaction.user.id})"), *changed],
                log_type="mod"
            )

    @bot.tree.command(name="automod-word-add", description="AutoMod yasak kelime listesine kelime ekler.")
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def automod_word_add(interaction, word: app_commands.Range[str, 2, 80]):
        words = add_banned_word(interaction.guild.id, str(word))
        await interaction.response.send_message(
            embed=make_embed("Yasak Kelime Eklendi", f"`{word}` listeye eklendi. Toplam: {len(words)}", 0x2ECC71),
            ephemeral=True
        )
        await log_event(
            interaction.guild,
            with_emoji("shield", "AutoMod Kelime Eklendi"),
            f"`{word}` yasak kelime listesine eklendi.",
            0x2ECC71,
            [("Yetkili", f"{interaction.user} ({interaction.user.id})")],
            log_type="mod"
        )

    @bot.tree.command(name="automod-word-remove", description="AutoMod yasak kelime listesinden kelime siler.")
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def automod_word_remove(interaction, word: app_commands.Range[str, 2, 80]):
        words = remove_banned_word(interaction.guild.id, str(word))
        await interaction.response.send_message(
            embed=make_embed("Yasak Kelime Silindi", f"`{word}` listeden silindi. Toplam: {len(words)}", 0xE67E22),
            ephemeral=True
        )
        await log_event(
            interaction.guild,
            with_emoji("shield", "AutoMod Kelime Silindi"),
            f"`{word}` yasak kelime listesinden silindi.",
            0xE67E22,
            [("Yetkili", f"{interaction.user} ({interaction.user.id})")],
            log_type="mod"
        )

    @bot.tree.command(name="automod-info", description="AutoMod ayarlarini gosterir.")
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def automod_info(interaction):
        await interaction.response.send_message(embed=automod_embed(interaction.guild), ephemeral=True)
