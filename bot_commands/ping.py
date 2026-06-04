from discord import app_commands


def register(bot):
    @bot.tree.command(name="ping", description="Bot gecikmesini gosterir.")
    @app_commands.guild_only()
    async def ping(interaction):
        await interaction.response.send_message(f"Pong! {round(bot.latency * 1000)}ms", ephemeral=True)
