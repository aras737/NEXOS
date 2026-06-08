import discord
from discord import app_commands

from core.embeds import make_embed
from core.emojis import with_emoji
from core.logging import log_event
from core.permissions import role_hierarchy_error, self_assign_role_permission_error
from core.storage import get_guild_setting, set_guild_setting


def channel_label(guild, channel_id):
    if not channel_id:
        return "Otomatik: adi kayit olan kanal"
    channel = guild.get_channel(int(channel_id))
    return channel.mention if channel else str(channel_id)


def role_label(guild, role_id):
    if not role_id:
        return "Otomatik: Uye/kayitli rolu varsa"
    role = guild.get_role(int(role_id))
    return role.mention if role else str(role_id)


def register(bot):
    @bot.tree.command(name="register-settings", description="Kayit kanalini, yas rolunu ve nick sistemini ayarlar.")
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.bot_has_permissions(
        manage_roles=True,
        manage_nicknames=True,
        send_messages=True,
        embed_links=True
    )
    @app_commands.describe(
        channel="Isim | Yas formatinin dinlenecegi kayit kanali.",
        registered_role="Kayit olan herkese verilecek ekstra rol.",
        clear_registered_role="Kayit rolunu temizler.",
        enabled="Kayit sistemini ac/kapat.",
        auto_create_age_roles="Yas rolu yoksa otomatik olusturulsun mu?"
    )
    async def register_settings(
        interaction,
        channel: discord.TextChannel | None = None,
        registered_role: discord.Role | None = None,
        clear_registered_role: bool | None = None,
        enabled: bool | None = None,
        auto_create_age_roles: bool | None = None
    ):
        changed = []

        if channel:
            set_guild_setting(interaction.guild.id, "registration_channel_id", channel.id)
            changed.append(("Kayit Kanali", f"{channel.mention} ({channel.id})"))

        if registered_role:
            error = role_hierarchy_error(interaction.guild, interaction.user, interaction.guild.me, registered_role)
            error = error or self_assign_role_permission_error(registered_role, "Kayit rolu")
            if error:
                await interaction.response.send_message(
                    embed=make_embed("Kayit Rolu Ayarlanamadi", error, 0xE74C3C),
                    ephemeral=True
                )
                return
            set_guild_setting(interaction.guild.id, "registration_registered_role_id", registered_role.id)
            changed.append(("Kayit Rolu", f"{registered_role.mention} ({registered_role.id})"))

        if clear_registered_role:
            set_guild_setting(interaction.guild.id, "registration_registered_role_id", None)
            changed.append(("Kayit Rolu", "Temizlendi"))

        if enabled is not None:
            set_guild_setting(interaction.guild.id, "registration_enabled", bool(enabled))
            changed.append(("Durum", "Acik" if enabled else "Kapali"))

        if auto_create_age_roles is not None:
            set_guild_setting(interaction.guild.id, "registration_create_age_roles", bool(auto_create_age_roles))
            changed.append(("Yas Rolu Otomatik", "Acik" if auto_create_age_roles else "Kapali"))

        current_channel_id = get_guild_setting(interaction.guild.id, "registration_channel_id")
        current_role_id = get_guild_setting(interaction.guild.id, "registration_registered_role_id")
        current_enabled = get_guild_setting(interaction.guild.id, "registration_enabled", True)
        current_age_roles = get_guild_setting(interaction.guild.id, "registration_create_age_roles", True)

        embed = make_embed(
            with_emoji("register", "Kayit Ayarlari"),
            "Kayit sistemi guncellendi." if changed else "Mevcut kayit ayarlari.",
            0x8B5CF6
        )
        embed.add_field(name="Durum", value="Acik" if current_enabled else "Kapali", inline=True)
        embed.add_field(name="Kanal", value=channel_label(interaction.guild, current_channel_id), inline=False)
        embed.add_field(name="Kayit Rolu", value=role_label(interaction.guild, current_role_id), inline=False)
        embed.add_field(name="Yas Rolu Otomatik", value="Acik" if current_age_roles else "Kapali", inline=True)
        embed.add_field(name="Format", value="`Isim | Yas`", inline=True)

        await interaction.response.send_message(embed=embed, ephemeral=True)
        if changed:
            await log_event(
                interaction.guild,
                with_emoji("register", "Kayit Ayarlari Guncellendi"),
                f"{interaction.user.mention} kayit ayarlarini guncelledi.",
                0x8B5CF6,
                [("Yetkili", f"{interaction.user} ({interaction.user.id})"), *changed],
                log_type="mod"
            )

    @bot.tree.command(name="register-panel", description="Kayit format panelini kanala gonderir.")
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.bot_has_permissions(send_messages=True, embed_links=True)
    @app_commands.describe(channel="Panelin gonderilecegi kanal. Bos birakirsan bu kanala atar.")
    async def register_panel(interaction, channel: discord.TextChannel | None = None):
        target = channel or interaction.channel
        embed = make_embed(
            with_emoji("register", "Kayit"),
            "Kayit icin su formati kullan:\n`Isim | Yas`\n\nYazdigin isim takma adin olur, yasina gore rolun verilir.",
            0x7C3AED
        )
        embed.set_footer(text="NEXOS Family kayit sistemi")

        await target.send(embed=embed)
        await interaction.response.send_message(
            embed=make_embed("Kayit Paneli Gonderildi", f"Panel {target.mention} kanalina gonderildi.", 0x2ECC71),
            ephemeral=True
        )
        await log_event(
            interaction.guild,
            with_emoji("register", "Kayit Paneli Gonderildi"),
            f"Kayit paneli {target.mention} kanalina gonderildi.",
            0x7C3AED,
            [("Yetkili", f"{interaction.user} ({interaction.user.id})")],
            log_type="mod"
        )
