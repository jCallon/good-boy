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

# Custom classes for keeping track of guild's user permissions for this bot
import discord_slash_commands.helpers.guild_permission as guild_permission
from discord_slash_commands.helpers.guild_permission import guild_permission_bank

# Import operating system module
import os

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

# Create string Discord uses to @mention people
def at(user_id: int) -> str:
    return f"<@{user_id}>"

# Assert the message author is the owner of this bot
def assert_author_is_bot_owner(app_ctx: discord.ApplicationContext) -> bool:
    return application_context_check(
        guild_permission.user_permission_bank.user_has_permission("bot owner", app_ctx.author.id, app_ctx.guild.id) == True,
        "You must be the bot owner to use this command." + \
        "\nThe bot owner is {at(guild_permission.get_bot_owner_discord_user_id())}.")

# Assert the message author has admin privelages for the bot in the guild this command is being called from
def assert_author_is_admin(app_ctx: discord.ApplicationContext) -> bool:
    return application_context_check(
        guild_permission_bank.user_has_permission("admin", app_ctx.author.id, app_ctx.guild.id) == True,
        "You must be one of my admins to use this command in this guild." + \
        "\nYou can get the list of my admins in this guild via `/settings admin list`.")

# Assert the message author is not blacklisted in the guild this command is being called from
def assert_author_is_not_blacklisted(app_ctx: discord.ApplicationContext) -> bool:
    return application_context_check(
        guild_permission_bank.user_has_permission("blacklisted", app_ctx.author.id, app_ctx.guild.id) == False,
        "You have been blacklisted from using most of my commands in this guild." + \
        "\nYou can get the list of admins you can appeal to via `/settings admin list`.")

# Assert the bot *is* accepting commands from non-admin users in the guild this command is being called from
def assert_bot_is_accepting_non_admin_commands(app_ctx: discord.ApplicationContext) -> bool:
    return application_context_check(
        guild_permission_bank.get_is_locked(app_ctx.guild.id) == False,
        "The bot must be accepting non-admin commands to use this command, which it currently isn't." + \
        "\nAn admin can reverse this via `/settings lock stop`.")

# Assert the bot *is not* accepting commands from non-admin users in the guild this command is being called from
def assert_bot_is_not_accepting_non_admin_commands(app_ctx: discord.ApplicationContext) -> bool:
    return application_context_check(
        guild_permission_bank.get_is_locked(app_ctx.guild.id) == True,
        "The bot must not be accepting non-admin commands to use this command, which it currently isn't." + \
        "\nAn admin can reverse this via `/settings lock start`.")

# Assert the message author is allowed to call the this command from their source
def assert_author_is_allowed_to_call_command(app_ctx: discord.ApplicationContext) -> bool:
    # If a command is not from a guild and does not require a guild (caught by guild_only=True), it's generally free-reign
    if app_ctx.guild == None:
        return True

    # Bot admins are always allowed to call commands within their guild
    if guild_permission_bank.user_has_permission("admin", app_ctx.author.id, app_ctx.guild.id) == True:
        return True

    # If the author is blacklisted in this guild, their command is not allowed
    if guild_permission_bank.user_has_permission("blacklisted", app_ctx.author.id, app_ctx.guild.id) == True:
        return assert_author_is_not_blacklisted(app_ctx)

    # The author called this from a guild, are not an admin in that guild, and are not blacklisted in that guild
    # Whether their command is allowed is up to whether the bot is currently accepting non-admin commands
    return assert_bot_is_accepting_non_admin_commands(app_ctx)
