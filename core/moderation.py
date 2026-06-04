from core.embeds import make_embed


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
        return "Sunucu sahibine islem yapamam."
    if member.top_role >= moderator.top_role and moderator != guild.owner:
        return "Bu uye senin rolunle ayni seviyede veya daha yukarida."
    if bot_member and member.top_role >= bot_member.top_role:
        return "Bu uye bot rolunden daha yukarida."
    return None
