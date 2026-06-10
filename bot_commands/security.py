from discord import app_commands

from core.embeds import make_embed
from core.emojis import with_emoji
from core.logging import log_event
from core.security import add_allowed_bot, allowed_bot_ids, remove_allowed_bot
from core.storage import get_guild_setting, set_guild_setting


def bool_text(value):
    return "Acik" if value else "Kapali"


def bot_list(guild):
    ids = allowed_bot_ids(guild.id)
    if not ids:
        return "Yok"
    lines = []
    for bot_id in ids[:30]:
        member = guild.get_member(int(bot_id))
        lines.append(f"{member.mention if member else bot_id} (`{bot_id}`)")
    return "\n".join(lines)


def security_embed(guild):
    enabled = get_guild_setting(guild.id, "security_enabled", True)
    bot_guard = get_guild_setting(guild.id, "security_bot_guard_enabled", True)
    anti_raid = get_guild_setting(guild.id, "security_anti_raid_enabled", True)
    threshold = get_guild_setting(guild.id, "security_raid_threshold", 3)
    window = get_guild_setting(guild.id, "security_raid_window_seconds", 30)

    embed = make_embed(
        with_emoji("shield", "Sunucu Koruma Ayarlari"),
        "Bot ekleme korumasi ve anti-raid sistemi.",
        0x8B5CF6
    )
    embed.add_field(name="Genel Durum", value=bool_text(enabled), inline=True)
    embed.add_field(name="Bot Guard", value=bool_text(bot_guard), inline=True)
    embed.add_field(name="Anti-Raid", value=bool_text(anti_raid), inline=True)
    embed.add_field(name="Raid Esigi", value=f"{threshold} olay / {window} sn", inline=True)
    embed.add_field(name="Izinli Botlar", value=bot_list(guild), inline=False)
    return embed


def parse_id(value):
    clean = str(value).strip().replace("<@", "").replace(">", "").replace("!", "")
    if not clean.isdigit():
        raise ValueError("ID sadece sayi olmali.")
    return int(clean)


def register(bot):
    @bot.tree.command(name="security-settings", description="Sunucu koruma ve bot ekleme korumasini ayarlar.")
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.bot_has_permissions(view_audit_log=True, manage_roles=True, kick_members=True, embed_links=True)
    async def security_settings(
        interaction,
        enabled: bool | None = None,
        bot_guard_enabled: bool | None = None,
        anti_raid_enabled: bool | None = None,
        raid_threshold: app_commands.Range[int, 2, 10] | None = None,
        raid_window_seconds: app_commands.Range[int, 10, 300] | None = None
    ):
        changed = []
        updates = {
            "enabled": enabled,
            "bot_guard_enabled": bot_guard_enabled,
            "anti_raid_enabled": anti_raid_enabled,
            "raid_threshold": raid_threshold,
            "raid_window_seconds": raid_window_seconds
        }
        for key, value in updates.items():
            if value is not None:
                set_guild_setting(interaction.guild.id, f"security_{key}", value)
                changed.append((key, bool_text(value) if isinstance(value, bool) else str(value)))

        await interaction.response.send_message(embed=security_embed(interaction.guild), ephemeral=True)
        if changed:
            await log_event(
                interaction.guild,
                with_emoji("shield", "Sunucu Koruma Ayarlari"),
                f"{interaction.user.mention} sunucu koruma ayarlarini guncelledi.",
                0x8B5CF6,
                [("Yetkili", f"{interaction.user} ({interaction.user.id})"), *changed],
                log_type="mod"
            )

    @bot.tree.command(name="security-allow-bot", description="Bir bot ID'sini izinli bot listesine ekler.")
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def security_allow_bot(interaction, bot_id: app_commands.Range[str, 15, 25]):
        try:
            parsed_id = parse_id(bot_id)
        except ValueError as error:
            await interaction.response.send_message(embed=make_embed("Gecersiz ID", str(error), 0xE74C3C), ephemeral=True)
            return

        add_allowed_bot(interaction.guild.id, parsed_id)
        await interaction.response.send_message(
            embed=make_embed("Bot Izinli Listeye Eklendi", f"`{parsed_id}` artik izinli bot.", 0x2ECC71),
            ephemeral=True
        )
        await log_event(
            interaction.guild,
            with_emoji("shield", "Bot Allowlist Eklendi"),
            f"`{parsed_id}` izinli bot listesine eklendi.",
            0x2ECC71,
            [("Yetkili", f"{interaction.user} ({interaction.user.id})")],
            log_type="mod"
        )

    @bot.tree.command(name="security-deny-bot", description="Bir bot ID'sini izinli bot listesinden siler.")
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def security_deny_bot(interaction, bot_id: app_commands.Range[str, 15, 25]):
        try:
            parsed_id = parse_id(bot_id)
        except ValueError as error:
            await interaction.response.send_message(embed=make_embed("Gecersiz ID", str(error), 0xE74C3C), ephemeral=True)
            return

        remove_allowed_bot(interaction.guild.id, parsed_id)
        await interaction.response.send_message(
            embed=make_embed("Bot Izinli Listeden Silindi", f"`{parsed_id}` artik izinli degil.", 0xE67E22),
            ephemeral=True
        )
        await log_event(
            interaction.guild,
            with_emoji("shield", "Bot Allowlist Silindi"),
            f"`{parsed_id}` izinli bot listesinden silindi.",
            0xE67E22,
            [("Yetkili", f"{interaction.user} ({interaction.user.id})")],
            log_type="mod"
        )

    @bot.tree.command(name="security-info", description="Sunucu koruma ayarlarini gosterir.")
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.bot_has_permissions(embed_links=True)
    async def security_info(interaction):
        await interaction.response.send_message(embed=security_embed(interaction.guild), ephemeral=True)
