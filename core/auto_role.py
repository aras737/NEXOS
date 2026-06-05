from core.logging import log_event
from core.storage import get_guild_setting


async def apply_auto_role(member):
    role_id = get_guild_setting(member.guild.id, "auto_role_id")
    if not role_id:
        return

    role = member.guild.get_role(int(role_id))
    if not role:
        await log_event(
            member.guild,
            "Oto Rol Hata",
            f"Oto rol bulunamadi: {role_id}",
            0xE74C3C
        )
        return

    try:
        await member.add_roles(role, reason="NEXOS oto rol")
        await log_event(
            member.guild,
            "Oto Rol Verildi",
            f"{member.mention} uyesine {role.mention} verildi.",
            0x2ECC71,
            [("Uye", f"{member} ({member.id})")]
        )
    except Exception as error:
        await log_event(
            member.guild,
            "Oto Rol Hata",
            f"{member} uyesine oto rol verilemedi.",
            0xE74C3C,
            [
                ("Rol", f"{role} ({role.id})"),
                ("Hata", f"{type(error).__name__}: {error}")
            ]
        )
