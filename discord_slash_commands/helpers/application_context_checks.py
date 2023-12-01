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

# Import user permissions for each guild
import discord_slash_commands.helpers.user_permission as user_perm

#==============================================================================#
# Define underlying structure                                                  #
#==============================================================================#

def at(user_id: int) -> str:
    """Create an @mention from user_id.

    To refer to a user uniquely and unabmiguously, you can @mention them. You
    can do this from a bot by formatting the user id in certain way.

    Args:
        user_id: The ID of the user to @mention

    Returns:
        A string that will @mention the given user when put in a message.
    """
    return f"<@{user_id}>"



def application_context_check(
    check_passed: bool,
    response_if_check_failed: str
) -> bool:
    """Handle custom application context check.

    If an application context check passed, return success, otherwise raise a
    CheckFailure with helpful explanations and suggested next steps.

    Args:
        check_passed: Whether the application context check passed
        response_if_check_failed: Payload to attach to discord.CheckFailure
            which will tell the message author what check failed and how to fix.

    Returns:
        Whether the passed in check passed.
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

    Args:
        ctx: The context the slash command using this check was called under

    Returns:
        Whether the check passed.
    """
    return application_context_check(
        len(ctx.bot.voice_clients) != 0 and \
            ctx.bot.voice_clients[0].is_connected(),
        "I must be connected to a voice chat to use this command." \
            + "\nPlease connect me to a voice chat to speak in via " \
            + "`/voice join`."
    )



def assert_bot_is_not_in_voice_chat(
    ctx: discord.ApplicationContext
) -> bool:
    """Assert the bot is not connected to voice chat.

    Assert the bot does not have an active connection established with any
    voice channel.

    Args:
        ctx: The context the slash command using this check was called under

    Returns:
        Whether the check passed.
    """
    return application_context_check(
        not(len(ctx.bot.voice_clients) != 0 and \
            ctx.bot.voice_clients[0].is_connected()),
        "I must not be connected to a voice chat to use this command." \
            + "\nPlease disconnect me from voice chat via `/voice leave`."
    )



def assert_bot_is_in_same_voice_chat_as_author(
    ctx: discord.ApplicationContext
) -> bool:
    """Assert the bot is in the same voice chat as the author of the command.

    Assert the message author is a member within the voice chat it is currently
    connected to.

    Args:
        ctx: The context the slash command using this check was called under

    Returns:
        Whether the check passed.
    """
    return application_context_check(
        assert_bot_is_in_voice_chat(ctx) and \
            (ctx.author in ctx.bot.voice_clients[0].channel.members),
        "You must be in the same voice chat as me to use this command." \
            + "\nPlease connect to my voice chat, or make me join your " \
            + "voice chat via `/voice leave` then `/voice join`."
    )



def assert_bot_is_playing_audio_in_voice_chat(
    ctx: discord.ApplicationContext
) -> bool:
    """Assert the bot is currently playing audio in voice chat.

    Assert the bot is in voice chat and is currently playing audio in it.

    Args:
        ctx: The context the slash command using this check was called under

    Returns:
        Whether the check passed.
    """
    return application_context_check(
        assert_bot_is_in_voice_chat(ctx) and \
            ctx.bot.voice_clients[0].is_playing(),
        "I must already be playing other audio to use this command." \
            + "\nThis can be done via many commands, such as `/tts play`."
    )



def assert_bot_is_not_playing_audio_in_voice_chat(
    ctx: discord.ApplicationContext
) -> bool:
    """Assert the bot is not currently playing audio in voice chat.

    Assert the bot is not in voice chat or is not currently playing audio in it.

    Args:
        ctx: The context the slash command using this check was called under

    Returns:
        Whether the check passed.
    """
    return application_context_check(
        not(assert_bot_is_in_voice_chat(ctx) and \
            ctx.bot.voice_clients[0].is_playing()),
        "I must not already be playing other audio to use this command." \
            + "\nPlease wait until I finish playing my current audio, or " \
            + "stop my current audio via `/voice queue remove`."
    )



def assert_author_is_bot_owner(
    ctx: discord.ApplicationContext
) -> bool:
    """Assert the message author is the owner of this bot.

    Assert the user ID of the message author is the same as the member ID of the
    bot owner.

    Args:
        ctx: The context the slash command using this check was called under

    Returns:
        Whether the check passed.
    """
    return application_context_check(
        ctx.author.id == user_perm.get_bot_owner_discord_user_id(),
        "You must be the bot owner to use this command." \
            + "\nThe bot owner is " \
            + f"{at(user_perm.get_bot_owner_discord_user_id())}."
    )



def assert_author_is_admin(
    ctx: discord.ApplicationContext
) -> bool:
    """Assert the message author is an admin in this guild.

    Assert the message author has admin privelages for the bot in the guild this
    slash command is being called from.

    Args:
        ctx: The context the slash command using this check was called under

    Returns:
        Whether the check passed.
    """
    user_permission = user_perm.UserPermission(ctx)
    return application_context_check(
        ctx.author.id == user_perm.get_bot_owner_discord_user_id() or
            user_permission.is_admin is True,
        "You must be one of my admins to use this command in this guild." \
            + "\nYou can get the list of my admins in this guild via " \
            + "`/permissions view permission: admin`."
    )



def assert_author_is_not_blacklisted(
    ctx: discord.ApplicationContext
) -> bool:
    """Assert the author is not blacklisted in this guild.

    Assert the message author is not blacklisted from using this bot in the
    guild this slash command is being called from.

    Args:
        ctx: The context the slash command using this check was called under

    Returns:
        Whether the check passed.
    """
    user_permission = user_perm.UserPermission(ctx)
    return application_context_check(
        user_permission.is_blacklisted is False,
        "You are blacklisted from using most of my commands in this guild." \
            + "\nYou can get the list of admins you can appeal to via " \
            + "`/permissions view permission: admin`."
    )



def assert_author_is_allowed_to_call_command(
    ctx: discord.ApplicationContext
) -> bool:
    """Assert the message author is allowed to call the this command.

    Assert the command, based on where it was called from and the permissions of
    its author, is allowed to be executed in this case. For example, when a
    command is called by someone who is blacklisted in the same server as where
    they're calling the command from, they should never be allowed to execute
    most commands.

    Args:
        ctx: The context the slash command using this check was called under

    Returns:
        Whether the check passed.
    """
    # The bot owner can do anything they want with the bot
    if ctx.author.id == user_perm.get_bot_owner_discord_user_id():
        return True

    # If a command is not from a guild and does not require a guild
    # (caught by guild_only=True), it's generally free-reign
    if ctx.guild is None:
        return True

    # Get the current UserPermissions of the author
    user_permission = user_perm.UserPermission(ctx)

    # Bot admins are always allowed to call commands within their guild
    if user_permission.is_admin is True:
        return True

    # If the author is blacklisted in this guild, their command is not allowed
    if user_permission.is_blacklisted is True:
        return assert_author_is_not_blacklisted(ctx)

    # The author called this from a guild, are not an admin in that guild,
    # and are not blacklisted in that guild. Whether their command is allowed
    # is up to whether the bot is currently accepting non-admin commands.
    # TODO: uncomment once feature is enabled
    #return assert_bot_is_accepting_non_admin_commands(ctx)
    return True



def assert_bot_audio_queue_length_is_non_zero(
    ctx: discord.ApplicationContext
) -> bool:
    """Assert the bot's audio queue length is non-zero.

    Assert the bot has an audio queue (this should only be possible when it is
    in voice chat) and the length of its audio queue greater than 0.

    Args:
        ctx: The context the slash command using this check was called under

    Returns:
        Whether the check passed.
    """
    audio_queue_list = ctx.bot.get_cog("AudioQueueList")
    return application_context_check(
        audio_queue_list is not None and len(audio_queue_list.queue) > 0,
        "There must be audio in my audio queue to use this command." \
            + "\nI clear my audio queue when I am not in voice chat."
    )
