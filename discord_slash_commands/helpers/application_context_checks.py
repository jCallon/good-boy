# ======================= #
# Import public libraries #
# ======================= #

# General discord API
import discord

# Import Callable object for more kinds of type hints
from typing import Callable

# =========================== #
# Define underlying structure #
# =========================== #

# Execute a check on the application_context, if it fails give the user a helpful message
def application_context_check(
    application_context: discord.ApplicationContext,
    check_function: Callable,
    response_if_check_function_fails: str
) -> bool:
    check_passed = check_function(application_context)
    if check_passed == False:
        failure = discord.CheckFailure
        failure.payload = response_if_check_function_fails
        raise failure
    return check_passed

# TODO: comment
def assert_bot_is_in_voice_chat(application_context: discord.ApplicationContext): 
    response_if_check_function_fails = "I must not be connected to a voice chat to use this command."
    response_if_check_function_fails += "\nPlease disconnect me from voice chat via \\voice leave."
    return application_context_check(
        application_context,
        lambda app_ctx: len(app_ctx.bot.voice_clients) != 0 and app_ctx.bot.voice_client.is_connected() == True,
        response_if_check_function_fails)

# TODO: comment
def assert_bot_is_not_in_voice_chat(application_context: discord.ApplicationContext):
    response_if_check_function_fails = "I must be connected to a voice chat to use this command."
    response_if_check_function_fails += "\nPlease connect me to a voice channel to speak in via \\voice join."
    return application_context_check(
        application_context,
        lambda app_ctx: len(app_ctx.bot.voice_clients) == 0 or app_ctx.bot.voice_client.is_connected() == False,
        response_if_check_function_fails)

# TODO: comment
def assert_bot_is_in_same_voice_chat_as_user(application_context: discord.ApplicationContext):
    response_if_check_function_fails = "You must be in the same voice chat as me to use this command."
    response_if_check_function_fails += "\nPlease connect to the voice chat I am in, or make me join your voice channel via \\voice leave then \\voice join."
    return application_context_check(
        application_context,
        lambda app_ctx: assert_bot_is_in_voice_chat(app_ctx) == True and app_ctx.bot.voice_clients[0].voice_channel.get_member(app_ctx.author.id) != None,
        response_if_check_function_fails)

# TODO: comment
def assert_bot_is_playing_audio_in_voice_chat(application_context: discord.ApplicationContext):
    response_if_check_function_fails = "I must already be playing other audio to use this command."
    response_if_check_function_fails += "\nThis can be done with many commands, such as \\tts play."
    return application_context_check(
        application_context,
        lambda app_ctx: not(assert_bot_is_in_voice_chat(app_ctx) == True and app_ctx.bot.voice_client.is_playing() == True),
        response_if_check_function_fails)

# TODO: comment
def assert_bot_is_not_playing_audio_in_voice_chat(application_context: discord.ApplicationContext):
    response_if_check_function_fails = "I must not already be playing other audio to use this command."
    response_if_check_function_fails += "\nPlease wait until I finish playing my current audio, or stop my current audio via \\voice stop."
    return application_context_check(
        application_context,
        lambda app_ctx: assert_bot_is_in_voice_chat(app_ctx) == True and app_ctx.bot.voice_client.is_playing() == True,
        response_if_check_function_fails)
