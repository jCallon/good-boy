"""Checks for validating PyCord.SlashCommand are allowed to be run.

This file defines checks which can be used in the PyCord.SlashCommand decorators
for validating the state of the bot and author are valid for the command a
member is trying to call.
"""

#==============================================================================#
# Import libraries                                                             #
#==============================================================================#

# Import Discord Python API
import discord

#==============================================================================#
# Define underlying structure                                                  #
#==============================================================================#

def application_context_check(
    check_passed: bool,
    response_if_check_failed: str
) -> bool:
    """Handle custom application context check.

    If an application context check passed, return success, otherwise raise a
    CheckFailure with helpful explanations and suggested next steps.
    """
    if check_passed is False:
        failure = discord.CheckFailure
        failure.payload = response_if_check_failed
        raise failure
    return check_passed



def assert_bot_is_in_voice_chat(
    ctx: discord.ApplicationContext
) -> bool:
    """Assert the bot is connected to voice chat.

    Assert the bot has an active connection established with a voice channel.
    """
    return application_context_check(
        len(ctx.bot.voice_clients) != 0 and \
        ctx.bot.voice_clients[0].is_connected(),
        "I must be connected to a voice chat to use this command." + \
         "\nPlease connect me to a voice chat to speak in via `/voice join`.")



def assert_bot_is_not_in_voice_chat(
    ctx: discord.ApplicationContext
) -> bool:
    """Assert the bot is not connected to voice chat.

    Assert the bot does not have an active connection established with any
    voice channel.
    """
    return application_context_check(
        not(len(ctx.bot.voice_clients) != 0 and \
            ctx.bot.voice_clients[0].is_connected()),
        "I must not be connected to a voice chat to use this command." + \
        "\nPlease disconnect me from voice chat via `/voice leave`.")



def assert_bot_is_in_same_voice_chat_as_author(
    ctx: discord.ApplicationContext
) -> bool:
    """Assert the bot is in the same voice chat as the author of the command.

    Assert the message author is a member within the voice chat it is currently
    connected to.
    """
    return application_context_check(
        assert_bot_is_in_voice_chat(ctx) and \
        (ctx.author in ctx.bot.voice_clients[0].channel.members),
        "You must be in the same voice chat as me to use this command." + \
        "\nPlease connect to my voice chat, or make me join your voice " + \
        "chat via `/voice leave` then `/voice join`.")



def assert_bot_is_playing_audio_in_voice_chat(
    ctx: discord.ApplicationContext
) -> bool:
    """Assert the bot is currently playing audio in voice chat.

    Assert the bot is in voice chat and is currently playing audio in it.

    Args:
        ctx: The context this SlashCommand was called under
    """
    return application_context_check(
        assert_bot_is_in_voice_chat(ctx) and \
        ctx.bot.voice_clients[0].is_playing(),
        "I must already be playing other audio to use this command." + \
        "\nThis can be done via many commands, such as `/tts play`.")



def assert_bot_is_not_playing_audio_in_voice_chat(
    ctx: discord.ApplicationContext
) -> bool:
    """Assert the bot is not currently playing audio in voice chat.

    Assert the bot is not in voice chat or is not currently playing audio in it.

    Args:
        ctx: The context this SlashCommand was called under
    """
    return application_context_check(
        not(assert_bot_is_in_voice_chat(ctx) and \
            ctx.bot.voice_clients[0].is_playing()),
        "I must not already be playing other audio to use this command." + \
        "\nPlease wait until I finish playing my current audio, or stop my " + \
        "current audio via `/voice stop`.")
