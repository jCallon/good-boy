# ======================= #
# Import public libraries #
# ======================= #

# General discord API
import discord

# Import Callable object for more kinds of type hints
from typing import Callable

# Custom classes for keeping track of user's permissions for this bot
import discord_slash_commands.helpers.permissions as permissions

# =========================== #
# Define underlying structure #
# =========================== #

# Execute a check on the application_context, if it fails give the author a helpful message
def application_context_check(
    check_passed: bool,
    response_if_check_failed: str
) -> bool:
    if check_passed == False:
        failure = discord.CheckFailure
        failure.payload = response_if_check_failed
        raise failure
    return check_passed

# Assert the bot *is* in voice chat
def assert_bot_is_in_voice_chat(app_ctx: discord.ApplicationContext) -> bool:
    return application_context_check(
        len(app_ctx.bot.voice_clients) != 0 and app_ctx.bot.voice_clients[0].is_connected(),
        "I must be connected to a voice chat to use this command." + \
         "\nPlease connect me to a voice channel to speak in via `/voice join`.")

# Asser the bot *is not* in voice chat
def assert_bot_is_not_in_voice_chat(app_ctx: discord.ApplicationContext) -> bool:
    return application_context_check(
        not(len(app_ctx.bot.voice_clients) != 0 and app_ctx.bot.voice_clients[0].is_connected()),
        "I must not be connected to a voice chat to use this command." + \
        "\nPlease disconnect me from voice chat via `/voice leave`.")

# Assert the bot *is in the same voice channel* as the message author
def assert_bot_is_in_same_voice_chat_as_author(app_ctx: discord.ApplicationContext) -> bool:
    return application_context_check(
        assert_bot_is_in_voice_chat(app_ctx) and (app_ctx.author in app_ctx.bot.voice_clients[0].channel.members),
        "You must be in the same voice chat as me to use this command." + \
        "\nPlease connect to the voice chat I am in, or make me join your voice channel via `/voice leave` then `/voice join`.")

# Assert the bot *is* playing audio in voice chat
def assert_bot_is_playing_audio_in_voice_chat(app_ctx: discord.ApplicationContext) -> bool:
    return application_context_check(
        assert_bot_is_in_voice_chat(app_ctx) and app_ctx.bot.voice_clients[0].is_playing(),
        "I must already be playing other audio to use this command." + \
        "\nThis can be done with many commands, such as `/tts play`.")

# Assert the bot *is not* playing audio in voice chat
def assert_bot_is_not_playing_audio_in_voice_chat(app_ctx: discord.ApplicationContext) -> bool:
    return application_context_check(
        not(assert_bot_is_in_voice_chat(app_ctx) and app_ctx.bot.voice_clients[0].is_playing()),
        "I must not already be playing other audio to use this command." + \
        "\nPlease wait until I finish playing my current audio, or stop my current audio via `/voice stop`.")

# Create string Discord uses to @mention people
def at(user_id: int) -> str:
    return f"<@{user_id}>"

# Assert the message author is the owner of this bot
def assert_author_is_bot_owner(app_ctx: discord.ApplicationContext) -> bool:
    return application_context_check(
        permissions.user_permission_bank.user_has_permission("bot owner", app_ctx.author.id, app_ctx.guild.id),
        "You must be the bot owner to use this command." + \
        "\nThe bot owner is {at(dotenv.bot_owner_discord_user_id)}.")

# Assert the message author has admin privelages for the bot in the guild this command is being called from
def assert_author_is_admin(app_ctx: discord.ApplicationContext) -> bool:
    bot_admin_user_id_list = permissions.get_user_permission(app_ctx.guild.id)
    bot_admin_string = ""
    for user_id in bot_admin_user_id_list:
        bot_admin_string += " " + at(user_id)
    return application_context_check(
        permissions.user_permission_bank.user_has_permission("admin", app_ctx.author.id, app_ctx.guild.id),
        "You must be a bot admin to use this command in this guild." + \
        "\nThe bot admins in this guild are" + bot_admin_string + ".")

# Assert the message author *is not* blacklisted in the guild this command is being called from
def assert_author_is_not_blacklisted(app_ctx: discord.ApplicationContext) -> bool:
    bot_admin_user_id_list = permissions.get_user_permission(app_ctx.guild.id)
    appeal_string = " " + at(dotenv.bot_owner_discord_user_id)
    for user_id in bot_admin_user_id_list:
        appeal_string += " " + at(user_id)
    return application_context_check(
        permissions.user_permission_bank.user_has_permission("blacklisted", app_ctx.author.id, app_ctx.guild.id),
        "You have been blacklisted from using any of my commands in this guild." + \
        "\nThe bot owner / admins you can appeal to are:" + appeal_string + ".")

# TODO: per-guild, save in file, perhaps userpermissions, instead, to be mutli-thread safe
global bot_is_accepting_non_admin_commands
bot_is_accepting_non_admin_commands = True

# TODO: comment
def assert_bot_is_accepting_non_admin_commands(app_ctx: discord.ApplicationContext) -> bool:
    global bot_is_accepting_non_admin_commands
    return application_context_check(
        bot_is_accepting_non_admin_commands == True,
        "The bot must paused to use this command." + \
        "\nYou can unpause the bot with `/bot_state unpause`.")

# TODO: comment
def assert_bot_is_not_accepting_non_admin_commands(app_ctx: discord.ApplicationContext) -> bool:
    global bot_is_accepting_non_admin_commands
    return application_context_check(
        bot_is_accepting_non_admin_commands == False,
        "The bot must paused to use this command." + \
        "\nYou can unpause the bot with `/bot_state unpause`.")

# TODO: comment
def assert_author_is_allowed_to_call_command(app_ctx: discord.ApplicationContext) -> bool:
    # If a command is not from a guild and does not require a guild (caught by guild_only=True), it's free-reign
    if app_ctx.guild == None:
        return True
    # Bot admins are always allowed to call commands within their guild
    elif permissions.user_has_permisson("admin", app_ctx.author.id, app_ctx.guild.id) == True:
        return True

    # If the author is blacklisted in this guild, their command is not allowed
    if permissions.user_has_permisson("blacklisted", app_ctx.author.id, app_ctx.guild.id) == True:
        return assert_author_is_not_blacklisted()

    # The author called this from guild, are not an admin in the guild, and are not blacklisted in the guild
    # Whether their command is allowed is up to whether the bot is currently accepting non-admin commands
    return assert_bot_is_accepting_non_admin_commands()
