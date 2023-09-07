# ======================= #
# Import public libraries #
# ======================= #

# General discord API
import discord

# =========================== #
# Define underlying structure #
# =========================== #

# Silas currently only supports being in one voice chat at a time



# Create slash command group
voice_slash_command_group = discord.SlashCommandGroup("voice", "Voice state commands")



# Define function for letting user connect the bot to voice chat
@voice_slash_command_group.command(name="join", description="Have me join the voice chat you are in.")
async def voice_join(ctx):
    # Determine if the user state is valid
    # If the user's state isn't valid, give them verbose error messages
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.respond(f"Please join a voice channel. I join the channel you are in.")
        return False

    # If we got here, the user state is valid and safe to act upon
    # Leave all other voice clients and join the user's, TODO playing a high bark on entry
    while len(ctx.voice_clients) > 0:
        await ctx.voice_clients[0].disconnect()
    ctx.author.voice.channel.connect()

    ctx.respond(f"I have tried to connect to your voice channel.")
    return True


# Define function for letting user disconnect the bot from voice chat
@voice_slash_command_group.command(name="leave", description="Have me leave the voice chat you are in.")
async def voice_leave(ctx):
    # Determine if the user and bot state is valid
    # If the user or bot's state isn't valid, give them verbose error messages
    if len(ctx.voice_clients) == 0:
        await ctx.respond(f"I am already not in a voice channel.")
        return False
    if not (ctx.author.voice and ctx.author.voice.channel and ctx.author.voice.channel == ctx.voice_clients[0].channel):
        await ctx.respond(f"Please join the voice channel you wish for me to leave.")
        return False

    # If we got here, the user and bot state is valid and safe to act upon
    # Leave the current voice channel, TODO giving a low bark on exit
    await ctx.voice_clients[0].disconnect()

    ctx.respond(f"I have tried to disconnect from your voice channel.")
    return True


# Define function for letting user connect stop the current audio being played
# TODO: support audio queue instead of only being able to play one thing at a time
@voice_slash_command_group.command(name="stop", description="Have me stop playing whatever audio I am currently playing.")
async def voice_stop(ctx):
    # Determine if the user and bot state is valid
    # If the user or bot's state isn't valid, give them verbose error messages
    if len(ctx.voice_clients) == 0:
        await ctx.respond(f"I am not in a voice channelm I have no audio to stop.")
        return False
    if not (ctx.author.voice and ctx.author.voice.channel and ctx.author.voice.channel == ctx.voice_clients[0].channel):
        await ctx.respond(f"Please join the voice channel you wish for me to stop playing audio in.")
        return False

    # If we got here, the user and bot state is valid and safe to act upon
    # Stop the playing of the audio currently playing in voice chat
    await ctx.voice_clients[0].stop()

    ctx.respond(f"I have tried to stop the audio I am playing in your voice channel.")
    return True
