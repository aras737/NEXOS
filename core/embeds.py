import discord


def make_embed(title, description, color=0x5865F2):
    return discord.Embed(title=title, description=description, color=color)
