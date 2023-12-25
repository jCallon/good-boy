"""PyCord.SlashCommand for using TTS in voice chat.

This file defines slash commands for letting a member have audio said on their
behalf, generated from text of their choosing, in the guild voice chat they are
currently connected to. You can also change the name TTS refers to you by and
what language you want your text spoken as.
"""

#==============================================================================#
# Import libraries                                                             #
#==============================================================================#

# Import API for using Google to turn text into speech
import gtts

# Import Discord Python API
import discord

# Import functions for asserting bot state
import discord_slash_commands.helpers.application_context_checks as ctx_check

# Import helper for queueing audio in voice chat
from discord_slash_commands.helpers import audio_queue

# Import helper for interacting with internal database
from discord_slash_commands.helpers import sqlite

# Import helper for managing new files
from discord_slash_commands.helpers import file_cache

# Import user permissions for each guild
import discord_slash_commands.helpers.user_permission as user_perm

#==============================================================================#
# Define underlying structure                                                  #
#==============================================================================#

# Define some constants for readability and to avoid copy/paste
MAX_SPOKEN_NAME_LEN = 20



class TTSUserPreference():
    """Define an instance of info held on a user for TTS.

    Define an instance of information held on a user for TTS. Information is
    held per-guild, where each guild has its own table, guild_$guild_id.

    Attributes:
        guild_id: The unique identifier of the guild the user has or is setting
            non-default TTS preferences for. For example, 1054409312894783901.
        user_id: The unique identifier of the user who has or is setting
            non-default TTS preferences. For example, 465014452489129824.
        spoken_name: The name the user prefers is spoken when TTS is announcing
            the author of the message about to be spoken. Useful for names with
            emojis or that are pronounced odd. For example, if you name is
            Choco<3, you might want the bot to pronounce your name as Chalko
            Heart, instead of Chocoh Less Than Three.
        language: The IETF code of the language the user prefers TTS to speak in
            for them. For example, "en" = English, and "ja" = Japanese. See
            https://gtts.readthedocs.io/en/latest/module.html for more info.
    """
    def __init__(self, ctx: discord.ApplicationContext):
        """Initialize this TTSUserPreference.

        Set the members of this TTSUserPreference based on members from ctx.

        Args:
            self: This TTSUserPreference
            ctx: The context the a TTS command was called from, must include
                a command author
        """
        # Fill self.guild_id
        # Sometimes a command will be sent from DMs, so it will not have a guild
        self.guild_id = ctx.guild.id if ctx.guild is not None else None

        # Fill self.user_id
        self.user_id = ctx.author.id

        # Fill self.spoken_name
        # Sometimes a command will be sent from DMs, so it will be from a
        # discord.User, instead of a discord.Member. User and Member fields
        # may not always be populated either.
        if isinstance(ctx.author, discord.Member) and \
            isinstance(ctx.author.nick, str):
            self.spoken_name = ctx.author.nick
        elif isinstance(ctx.author.display_name, str):
            self.spoken_name = ctx.author.display_name
        elif isinstance(ctx.author.name, str):
            self.spoken_name = ctx.author.name
        else:
            self.spoken_name = f"{self.user_id}"

        # Fill self.language
        # Just use a default value of English
        self.language = "en"

    def save(self) -> bool:
        """Save this TTSUserPreference instance into the database.

        Insert this TTSUserPreference into the tts_info database. Each guild
        has its own table named after its guild id. If a TTSUserPreference with
        the same user_id already exists in the table, just update its
        spoken_name and language to match this TTSUserPreference.

        Args:
            self: This TTSUserPreference

        Returns:
            Whether the operation was successful. It may not be, for example,
            if the connection to the database, or the database itself, is not
            found or is faulty.
        """
        # Execute SQL query
        # TODO: Why does this return
        #       sqlite3.OperationalError: near "?": syntax error
        #       I want to use this instead of the below
        #return [] != sqlite.run(
        #    file_name = "tts_info",
        #    query = "INSERT INTO ? VALUES (?,?,?) " \
        #        + "ON CONFLICT(user_id) " \
        #        + "DO UPDATE SET spoken_name=?,language=?",
        #    query_parameters = (
        #        f"guild_{self.guild_id}",
        #        self.user_id,
        #        self.spoken_name,
        #        self.language,
        #        self.spoken_name,
        #        self.language
        #    ),
        #    commit = True
        #)

        # Check safety of parameters
        if not (
            isinstance(self.guild_id, int) and \
            isinstance(self.user_id, int) and \
            isinstance(self.spoken_name, str) and \
            isinstance(self.language, str)
        ):
            return False

        # Execute SQL query
        return sqlite.run(
            file_name = "tts_info",
            query = f"INSERT INTO guild_{self.guild_id} VALUES "\
                + f"({self.user_id},?,?) ON CONFLICT(user_id) " \
                + "DO UPDATE SET spoken_name=?,language=?",
            query_parameters = (
                self.spoken_name,
                self.language,
                self.spoken_name,
                self.language
            ),
            commit = True
        ).success is True


    def read(self, guild_id: int, user_id: int) -> bool:
        """Copy TTSUserPreference matching guild_id and user_id from database.

        Try to find the row in the table guild_$guild_id matching user_id for
        the TTS user information database. If it exists, overwrite the members
        of this TTSUserPreference with its data entries.

        Args:
            self: This TTSUserPreference
            guild_id: Users may have preferences that differ per guild. This
                parameter lets you specify the guild you are checking this
                user's preferences for.
            user_id: The ID of the user you want to know the preferences of.

        Returns:
            Whether the operation was successful. It may not be, for example,
            if the connection to the database, or the database itself, is not
            found or is faulty. Or, this user simply does not have preferences
            in this guild.
        """
        # TODO: Why does this return
        #       sqlite3.OperationalError: near "?": syntax error
        #       I want to use this instead of the below
        #result = sqlite.run(
        #    file_name = "tts_info",
        #    query = "SELECT user_id,spoken_name,language " \
        #        + "FROM ? WHERE user_id=?",
        #    query_parameters = (
        #        f"guild_{self.guild_id}",
        #        self.user_id
        #    ),
        #    commit = False
        #)

        # Check safety of parameters
        if not (isinstance(guild_id, int) and isinstance(user_id, int)):
            return False

        # Execute SQL query
        status = sqlite.run(
            file_name = "tts_info",
            query = "SELECT user_id,spoken_name,language FROM " \
                + f"guild_{guild_id} WHERE user_id={user_id}",
            query_parameters = (),
            commit = False
        )

        # If there was no match, return failure and don't change this
        # TTSUserPreference's members
        if status.success is False:
            return False

        # There was a match, overwrite this TTSUserPreference's members with
        # values from the database
        result = status.result[0]
        self.guild_id = guild_id
        self.user_id = user_id
        self.spoken_name = result[1]
        self.language = result[2]
        return True



# Create class instances
tts_file_cache = file_cache.FileCacheList(
    directory = "tts",
    max_bytes = 20*1000000
)



# Create TTS slash command group
tts_slash_command_group = discord.SlashCommandGroup(
    checks = [ctx_check.assert_author_is_allowed_to_call_command],
    #default_member_permissions = default,
    description = "Text to speech commands",
    #description_localizations = default,
    #guild_ids = default,
    guild_only = True,
    name = "tts",
    #name_localizations = default,
    #nsfw = default,
    #parent = default
)



# Set default TTS volume, ex. 2 = 200%
TTS_DEFAULT_VOLUME = 2.0



def make_tts_audio_file(
    text_to_say : str,
    language_to_speak : str
) -> str:
    """Download audio for the text_to_say in language_to_speak from gtts.

    Download TTS audio for text_to_say and language_to_speak if it doesn't
    already exist, then return the path to the file containing the audio.

    Args:
        text_to_say: The text to say in TTS
        language_to_speak: The language to speak text_to_say in

    Returns:
        A string containing the path to the file containing to TTS audio.
    """
    # Generate file name for text_to_say and language_to_speak
    file_name = tts_file_cache.get_hashed_file_name(
        content_to_hash = (text_to_say, language_to_speak),
        file_extension = "mp3"
    )

    # If the file is not already downloaded, download it
    if not tts_file_cache.file_exists(file_name):
        speech_from_text = gtts.tts.gTTS(
            text=text_to_say,
            lang=language_to_speak
        )
        speech_from_text.save(f"{file_cache.CACHE_DIR}/{file_name}")
        # TODO: error should never happen, but add check anyways
        tts_file_cache.add(file_name = file_name, normalize_audio = True)

    # Return file path with generated audio
    return tts_file_cache.get_file_path(file_name)



# Define function for letting user say text in voice chat
# TODO: make DM messages that are just text and not slash commands be
# interpretted as TTS, while not letting them avoid blacklisting
# NOTE: gtts' write_to_fp() theoretically avoids writing to file?
@tts_slash_command_group.command(
    name="play",
    description="Make me say certain text on your behalf in your voice chat.",
    guild_only = False,
    checks=[
        ctx_check.assert_bot_is_in_voice_chat,
        ctx_check.assert_bot_is_in_same_voice_chat_as_author
    ]
)
async def tts_play(
    ctx,
    text_to_say: discord.Option(
        str,
        description="The text you want said on your behalf in voice chat."
    )
):
    """Tell bot to say text_to_say in voice chat.

    Make bot generate audio for text_to_say, then play it in its current
    voice chat, prefaced by the author of this command.

    Args:
        ctx: The context this SlashCommand was called under
        text_to_say: The text to say in voice chat
    """
    # Determine if the author's arguments are valid
    err_msg = ""
    if len(text_to_say) < 0:
        err_msg += "\nPlease give me more than 0 characters to say."
    if len(text_to_say) > 500:
        err_msg += "\nPlease break your text into segments of <=500 characters."

    # If the author's arguments were invalid,
    # give them verbose error messages and an example to help them
    if err_msg != "":
        err_msg += "\nHere's an example command."
        err_msg += "\nGreet everyone in voice chat."
        err_msg += "\n`/tts play text_to_say: Hi everyone!`"
        await ctx.respond(ephemeral=True, content=err_msg)
        return False

    # Determine if the author's TTS preferences are still valid
    tts_user_preference = TTSUserPreference(ctx)
    tts_user_preference.read(ctx.guild.id, ctx.author.id)
    if len(tts_user_preference.spoken_name) > MAX_SPOKEN_NAME_LEN:
        err_msg += "\nYour current preferred spoken name, " \
            + f"{tts_user_preference.spoken_name}, must be " \
            + f"<={MAX_SPOKEN_NAME_LEN} characters." \
            + "\nPlease change it via `/tts spoken_name`."
    if tts_user_preference.language not in gtts.lang.tts_langs():
        err_msg += f"\nYour TTS language, {tts_user_preference.language}, is " \
            + "not supported anymore." \
            + "\nPlease change it via `/tts language`."

    # If the bot state wasn't valid,
    # give the author verbose error messages to help them
    if err_msg != "":
        await ctx.respond(ephemeral=True, content=err_msg)
        return False

    # If we got here, the arguments and bot state should be valid and safe to
    # act upon.

    # Get/create audio file for name
    name_audio_file_path = make_tts_audio_file(
        text_to_say=tts_user_preference.spoken_name,
        language_to_speak=tts_user_preference.language
    )
    # Get/create audio file for text
    text_audio_file_path = make_tts_audio_file(
        text_to_say=text_to_say,
        language_to_speak=tts_user_preference.language
    )

    # Pull audio queue
    audio_queue_list = ctx.bot.get_cog("AudioQueueList")
    # Queue name
    name_audio_queue_element_id = audio_queue_list.add(
        ctx = ctx,
        description = tts_user_preference.spoken_name,
        file_path = name_audio_file_path,
        priority = audio_queue.HIGH_PRIORITY
    )
    # Queue text
    text_audio_queue_element_id = audio_queue_list.add(
        ctx = ctx,
        description = text_to_say,
        file_path = text_audio_file_path,
        priority = audio_queue.HIGH_PRIORITY
    )

    # If both name and text could be added to audio queue successfully,
    # and in the correct order, everything went well, exit early
    if name_audio_queue_element_id > -1 and \
        text_audio_queue_element_id > -1 and \
        text_audio_queue_element_id == name_audio_queue_element_id + 1:
        num_files_ahead = audio_queue_list.get_index_in_queue(
            audio_queue_element_id = name_audio_queue_element_id,
            priority = audio_queue.HIGH_PRIORITY
        )
        await ctx.respond(
            ephemeral = True,
            content = f"Queued `{tts_user_preference.spoken_name}` as ID " \
                + f"`{name_audio_queue_element_id}`, and `{text_to_say}` as " \
                + f"ID `{text_audio_queue_element_id}`." \
                + f"\nThere are {num_files_ahead} other high-priority "
                + "(priority level {audio_queue.HIGH_PRIORITY}) audio files " \
                + "ahead of you."
        )
        return True
    # If the name queued sucessfully, remove it, name and text must queue after
    # one another
    if name_audio_queue_element_id > -1:
        audio_queue_list.remove(name_audio_queue_element_id)
    # If the text queued sucessfully, remove it, name and text must queue after
    # one another
    if text_audio_queue_element_id > -1:
        audio_queue_list.remove(text_audio_queue_element_id)

    # Something went wrong in queuing the audio, despite generating the audio
    # fine, tell author
    await ctx.respond(
        ephemeral = True,
        content = "An internal error occured queuing your name and text_to_say."
    )
    return True



@tts_slash_command_group.command(
    name="spoken_name",
    description="Change the text I use to pronounce your name for TTS here."
)
async def tts_spoken_name(
    ctx,
    new_spoken_name: discord.Option(
        str,
        description="The name you want TTS to be refer to you by in this guild."
    )
):
    """Tell bot how to refer to you when using TTS in this guild.

    Change the name TTS refers to you by when announcing the author of a TTS
    message in this guild. Whether you want a different name entirely, or just
    to help TTS pronounce your name correctly is up to you.

    Args:
        ctx: The context this SlashCommand was called under
        new_spoken_name: The name you want TTS to refer to you by in this guild.
    """
    # Determine if the author's arguments are valid
    err_msg = ""
    if len(new_spoken_name) == 0:
        err_msg += "Please give me >0 characters for your preferred name."
    if len(new_spoken_name) > MAX_SPOKEN_NAME_LEN:
        err_msg += "Please give me a preferred name of " \
            + f"<={MAX_SPOKEN_NAME_LEN} characters."

    # If the author's arguments were invalid,
    # give them verbose error messages and an example to help them
    if err_msg != "":
        err_msg += "\nHere's an example command."
        err_msg += "\nHave TTS call me Tomato."
        err_msg += "\n`/tts spoken_name new_spoken_name: Toemahtoe`"
        await ctx.respond(ephemeral=True, content=err_msg)
        return False

    # If we got here, the arguments are valid and safe to act upon
    # Update tts_user_preference_bank
    tts_user_preference = TTSUserPreference(ctx)
    tts_user_preference.read(ctx.guild.id, ctx.author.id)
    tts_user_preference.spoken_name = new_spoken_name
    if tts_user_preference.save() is False:
        await ctx.respond(
            ephemeral=True,
            content="Could not save your new preference for unknown reasons."
                + "\nPlease tell the bot owner, " \
                + f"<@{user_perm.get_bot_owner_discord_user_id()}>, "
                + "to look into the issue."
                + "\nIn the meantime, you can change your nick in the guild "
                + "you're using this command for to get the same effect."
        )
        return False
    await ctx.respond(
        ephemeral=False,
        content=f"Set your preferred name for TTS to {new_spoken_name}."
    )
    return True



@tts_slash_command_group.command(
    name="language",
    description="Change the language/accent I speak in for you for TTS here."
)
async def tts_language(
    ctx,
    new_language: discord.Option(
        str,
        description="The language/accent you want TTS to speak in this guild."
    )
):
    """Tell bot what language to speak your TTS in this guild.

    Change the language TTS speaks for you in this guild.

    Args:
        ctx: The context this SlashCommand was called under
        new_language: The language you want TTS to speak in in this guild.
    """
    # Determine if the author's arguments are valid
    err_msg = ""
    if new_language not in gtts.lang.tts_langs():
        err_msg += "I do not know {new_language}." \
            + "\nI use IETF language tags to remember and distinguish " \
            + "between languages. For example, English = `en`." \
            + "\nPlease try to find the tag for your language from this " \
            + "list, if it's not present in this list I don't support it: `" \
            + ", ".join(gtts.lang.tts_langs()) \
            + "`\nLearn more at " \
            + "`https://en.wikipedia.org/wiki/IETF_language_tag`."

    # If the author's arguments were invalid,
    # give them verbose error messages and an example to help them
    if err_msg != "":
        err_msg += "\nHere's an example command." \
            + "\nHave TTS use English as my language." \
            + "\n`/tts language new_language: en`"
        await ctx.respond(ephemeral=True, content=err_msg)
        return False

    # If we got here, the arguments are valid and safe to act upon
    # Update tts_user_preference_bank
    tts_user_preference = TTSUserPreference(ctx)
    tts_user_preference.read(ctx.guild.id, ctx.author.id)
    tts_user_preference.language = new_language
    if tts_user_preference.save() is False:
        await ctx.respond(
            ephemeral=True,
            content="Could not save your new preference for unknown reasons."
                + "\nPlease tell the bot owner, " \
                + f"<@{user_perm.get_bot_owner_discord_user_id()}>, "
                + "to look into the issue."
                + "\nIn the meantime, you can change your nick in the guild "
                + "you're using this command for to get the same effect."
        )
        return False
    await ctx.respond(
        ephemeral=True,
        content=f"Set your language for TTS to {new_language}."
    )
    return True
