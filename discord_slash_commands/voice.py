"""PyCord.SlashCommand for altering PyCord Discord bot voice state.

This file defines slash commands for letting a member connect, disconnect, or
otherwise modify the voice state of the bot. These slash commands don't do much
themselves, but enable all other slash commands used by the bot that play or
otherwise interface with audio in voice chat.
"""

#==============================================================================#
# Import public libraries                                                      #
#==============================================================================#

# Import Discord Python API
import discord

# Import functions for asserting bot state
import discord_slash_commands.helpers.application_context_checks as ctx_check

#==============================================================================#
# Define underlying structure                                                  #
#==============================================================================#

# NOTE: This bot currently only supports being in one voice chat at a time,
# and all coding of this bot assumes this.



# Create voice slash command group
# TODO: Add admin/user permission checks
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



@voice_slash_command_group.command(
    name="join",
    description="Make me join your voice chat.",
    checks=[ctx_check.assert_bot_is_not_in_voice_chat]
)
async def voice_join(ctx):
    """Tell bot to join your voice chat.

    Connects bot to message author's voice chat, if bot is not already in a
    voice chat, and the message author is in a valid voice chat to join.

    Args:
        ctx: The context this SlashCommand was called under
    """
    # We join the author's voice chat, if they aren't in one, we can't act
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.respond(
            ephemeral = True,
            content = "Please join a voice chat. I join the chat you are in."
        )
        return False

    # Join the author's voice chat
    # TODO: Play a high bark on entry
    await ctx.author.voice.channel.connect()
    await ctx.respond(
        ephemeral = False,
        delete_after = 60*30,
        content = "I have tried to connect to your voice channel."
    )
    return True



@voice_slash_command_group.command(
    name="leave",
    description="Make me leave your voice chat.",
    checks=[
        ctx_check.assert_bot_is_in_voice_chat,
        ctx_check.assert_bot_is_in_same_voice_chat_as_author,
        ctx_check.assert_bot_is_not_playing_audio_in_voice_chat,
    ]
)
async def voice_leave(ctx):
    """Tell bot to leave your voice chat.

    Disconnect the bot from your voice chat if it's not busy playing audio.

    Args:
        ctx: The context this SlashCommand was called under
    """
    # Leave the author's voice chat
    # TODO: Play a low bark on exit
    await ctx.voice_client.disconnect()
    await ctx.respond(
        ephemeral=False,
        delete_after=60*30,
        content="I have tried to disconnect from your voice channel."
    )
    return True



# TODO: Support audio queue,
#       instead of only being able to play one audio at a time
@voice_slash_command_group.command(
    name="stop",
    description="Make me stop whatever audio I am playing in your voice chat.",
    checks=[
        ctx_check.assert_bot_is_in_voice_chat,
        ctx_check.assert_bot_is_in_same_voice_chat_as_author,
        ctx_check.assert_bot_is_playing_audio_in_voice_chat,
    ]
)
async def voice_stop(ctx):
    """Tell bot to stop currently playing audio.

    Make bot stop playing the audio it is currently playing in your voice chat.

    Args:
        ctx: The context this SlashCommand was called under
    """
    # Stop the playing of the audio currently playing in voice chat
    ctx.voice_client.stop()
    await ctx.respond(
        ephemeral=False,
        delete_after=60,
        content="I have tried to stop what was playing in your voice chat."
    )
    return True
