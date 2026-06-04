from discord import app_commands


def register(bot):
    @bot.tree.command(name="say", description="Bot adina mesaj gonderir.")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_messages=True)
    async def say(interaction, message: str):
        await interaction.channel.send(message)
        await interaction.response.send_message("Gonderildi.", ephemeral=True)
