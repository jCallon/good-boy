# ======================= #
# Import public libraries #
# ======================= #

# General discord API
import discord

# Custom functions for denying commands based off of bot state
import discord_slash_commands.helpers.application_context_checks as application_context_checks

# =========================== #
# Define underlying structure #
# =========================== #

# Silas currently only supports being in one voice chat at a time



# Create slash command group
voice_slash_command_group = discord.SlashCommandGroup(
    #checks = default,
    #default_member_permissions = default,
    description = "Voice state commands",
    #description_localizations = default,
    #guild_ids = default,
    guild_only = True,
    name = "voice",
    #name_localizations = default,
    #nsfw = default,
    #parent = default
)



# Define function for letting user connect the bot to voice chat
@voice_slash_command_group.command(
    name="join",
    description="Have me join the voice chat you are in.",
    checks=[
        application_context_checks.assert_bot_is_not_in_voice_chat,
    ]
)
async def voice_join(ctx):
    # Determine if the user state is valid
    # If the user's state isn't valid, give them verbose error messages
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.respond(f"Please join a voice channel. I join the channel you are in.")
        return False

    # If we got here, the user state is valid and safe to act upon
    # Join the user's voice chat, TODO playing a high bark on entry
    await ctx.author.voice.channel.connect()

    await ctx.respond(f"I have tried to connect to your voice channel.")
    return True


# Define function for letting user disconnect the bot from voice chat
@voice_slash_command_group.command(
    name="leave",
    description="Have me leave the voice chat you are in.",
    checks=[
        application_context_checks.assert_bot_is_in_voice_chat,
        application_context_checks.assert_bot_is_in_same_voice_chat_as_user,
        application_context_checks.assert_bot_is_not_playing_audio_in_voice_chat,
    ]
)
async def voice_leave(ctx):
    # Leave the current voice channel, TODO giving a low bark on exit
    await ctx.voice_client.disconnect()

    await ctx.respond(f"I have tried to disconnect from your voice channel.")
    return True


# Define function for letting user connect stop the current audio being played
# TODO: support audio queue instead of only being able to play one thing at a time
@voice_slash_command_group.command(
    name="stop",
    description="Have me stop playing whatever audio I am currently playing.",
    checks=[
        application_context_checks.assert_bot_is_in_voice_chat,
        application_context_checks.assert_bot_is_in_same_voice_chat_as_user,
        application_context_checks.assert_bot_is_playing_audio_in_voice_chat,
    ]
)
async def voice_stop(ctx):
    # Stop the playing of the audio currently playing in voice chat
    await ctx.voice_client.stop()

    await ctx.respond(f"I have tried to stop the audio I am playing in your voice channel.")
    return True
