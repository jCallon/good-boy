"""PyCord.SlashCommand for using TTS in voice chat.

This file defines slash commands for letting a member have audio said on their
behalf, generated from text of their choosing, in the guild voice chat they are
currently connected to. You can also change the name TTS refers to you by and
what language you want your text spoken as.
"""

#==============================================================================#
# Import libraries                                                             #
#==============================================================================#

# Import operating system API for things like moving files
import os

# Import API for hashing text in a collision-resistant way
import hashlib

# Import API for handling ascii strings as binary lists
import binascii

# Import Callable type
from typing import Callable

# Import API for using Google to turn text into speech
import gtts

# Import Discord Python API
import discord

# Import functions for asserting bot state
import discord_slash_commands.helpers.application_context_checks as ctx_check

# Import TODO
import discord_slash_commands.helpers.audio_queue as audio_queue

# Import TODO
import discord_slash_commands.helpers.sqlite as sqlite

#==============================================================================#
# Define underlying structure                                                  #
#==============================================================================#

class TTSUserPreference():
    """Define an instance of info held on a user for TTS.

    Define a row in ./db/tts_info.db that stores TTS preferences per member,
    per guild.

    Attributes:
        guild_id: The unique identifier for the guild the user is setting their
            preferences for. Lets users have per-guild settings. For example,
            1054409312894783901.
        user_id: The unique identifier for the user who has non-default TTS
            preferences. For example, 465014452489129824.
        spoken_name: The name the user prefers is spoken when TTS is announcing
            the author of the message about to be spone. Useful for names with
            emojis or that are pronounced odd. For example, if you name is
            Choco<3, you might want the bot to pronounce your name as Chalko
            Heart, instead of Chohco Less Than Three.
        language: The IETF code of the language the user prefers TTS to speak in
            for them. For example, "en" = English, and "ja" = Japanese. See
            https://gtts.readthedocs.io/en/latest/module.html for more info.
    """
    def __init__(
        self,
        ctx: discord.ApplicationContext
    ):
        """Initialize this TTSUserPreference.

        TODO.

        Args:
            self: This TTSUserPreference
            ctx: TODO
        """
        # Fill self.guild_id
        # Sometimes a command will be sent from DMs, so it will not have a guild
        self.guild_id = ctx.guild.id if ctx.guild != None else None

        # Fill self.user_id
        self.user_id = ctx.author.id

        # Fill self.spoken_name
        # Sometimes a command will be sent from DMs, so it will be from a
        # 'User', not a 'Member'. Fields will not always be populated either.
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
        ).success == True
        

    def read(self, guild_id: int, user_id: int) -> bool:
        """Copy TTSUserPreference matching guild_id and user_id from database.

        Try to find a TTSUserPreference matching guild_id and user_id in the
        database. Each guild has its own table named after its guild id.
        If it exists, overwrite the members of this TTSUserPreference with its
        data entries.

        Args:
            self: This TTSUserPreference
            guild_id: Users may have preferences that differ per guild. This
                parameter lets you specifies the guild you are checking this
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
        if status.success == False:
            return False
        
        # There was a match, overwrite this TTSUserPreference's members with
        # values from the database
        result = status.result[0]
        self.guild_id = guild_id
        self.user_id = user_id
        self.spoken_name = result[1]
        self.language = result[2]
        return True



class TTSFileInfo():
    """Define an instance of info held on an audio file generated for TTS.

    Define an class for holding the file information we care about for files
    generated by TTS: what the file's name was and when it was last accessed.

    Attributes:
        file_name: The name of an MP3 file holding audio generate for TTS,
            see TTSFileInfoList.get_file_name to see how they're generated
        last_access_time: The last time the file name self.file_name was
            accessed. This may not be the same as when it was made or last
            modified.
    """
    def __init__(self, file_name: str = "", last_access_time: int = 0):
        """Initialize this TTSFileInfo.

        Set the members of this TTSFileInfo to the passed in or default values.

        Args:
            self: This TTSUserPreference
            file_name: What initialize self.file_name as
            last_access_time: What initialize self.last_access_time as
        """
        self.file_name = file_name
        self.last_access_time = last_access_time



class TTSFileInfoList():
    """Define a list of all instance of info held on generated TTS audio files.

    Define an API for making PyCord-compatible audio sources for given text and
    language while keeping your computer clean.

    Attributes:
        file_directory: The directory audio generated from text for TTS will
            be saved. Assumes the directory is already created and will not
            create it for you.
        max_allowed_files: The max number of files allowed to be stored in
            self.file_directory. This is to prevent spam an bloat to the bot
            owner's computer.
    """
    def __init__(self, file_directory: str, max_allowed_files: int):
        """Initialize this TTSFileInfoList.

        Set the members of this TTSFileInfoList to the passed in or default
        values.

        Args:
            self: This TTSUserPreference
            file_directory: What initialize self.file_directory as
            max_allowed_files: What initialize self.max_allowed_files as
        """
        self.file_directory = file_directory
        self.max_allowed_files = max_allowed_files

    def get_file_name(self, text_to_say: str, language_to_speak: str) -> str:
        """Get the file name for TTS audio of a given language and content.

        Generate a file name to store TTS audio at based on what is being said
        and what language it is being spoken in.
        Used: https://cryptobook.nakov.com/cryptographic-hash-functions.
        Using a collision-resistant hash to not store plain text from arbitrary
        plaintext from an unknown source (hello embedded bash commands!), while
        also being able to identify if this file has been generated before.

        Args:
            self: This TTSUserPreferenceList
            text_to_say: That text will be said in the audio file.
            language_to_speak: What language the text will be spoken in in the
                audio file.

        Returns:
            The file name to read existing audio from or write new audio to.
        """
        byte_array = language_to_speak + text_to_say
        byte_array = byte_array.encode()
        return f"{binascii.hexlify(hashlib.sha3_256(byte_array).digest())}.mp3"

    def get_file_path(self, file_name: str) -> str:
        """Give the expected relative path of the file at file_name.

        Generate a relative file path from self.file_directory and file_name.

        Args:
            self: This TTSUserPreferenceList
            file_name: The name of the file you wish to prepend
                self.file_directory to

        Returns:
            The expected relative path of file_name.
        """
        return f"{self.file_directory}/{file_name}"

    def get_audio_source(
        self,
        text_to_say: str,
        language_to_speak: str
    ) -> discord.FFmpegPCMAudio:
        """Return a PyCord audio source for text_to_say and language_to_speak.

        Use GTTS to convert text_to_say for language_to_speak into an MP3 file.
        If a file for the same text_to_say and language_to_speak is already
        generated and saved onto this computer, use that instead of generating
        a new file. Then, give back a PyCord-compatible audio source for the
        file generated or that already existed.

        Args:
            self: This TTSUserPreferenceList
            text_to_say: The text TTS will try to say
            language_to_speak: The language TTS will try to say text_to_say in

        Returns:
            PyCord compatible audio source pointing to the TTS audio file.
        """
        # Get the file names and access times
        sorted_list_of_file_info = []
        for file_name in os.listdir(self.file_directory):
            sorted_list_of_file_info.append(TTSFileInfo(
                file_name,
                os.stat(self.get_file_path(file_name)).st_atime
            ))

        # Sort the files by access time
        sorted_list_of_file_info = sorted(
            sorted_list_of_file_info,
            key=lambda file_info: file_info.last_access_time
        )

        # Remove files once over self.max_allowed_files,
        # removing the least recently accessed files
        while len(sorted_list_of_file_info) >= self.max_allowed_files:
            os.path.remove(
                self.get_file_path(sorted_list_of_file_info[0].file_name)
            )
            sorted_list_of_file_info.pop(0)

        # Generate the file name and path for the 'new' TTS audio file
        file_name = self.get_file_name(text_to_say, language_to_speak)
        file_path = self.get_file_path(file_name)

        # See if there is already an audio file generated for this text_to_say
        # and language_to_speak
        file_exists = False
        for i in range(len(sorted_list_of_file_info)):
            if file_name == sorted_list_of_file_info[i].file_name:
                file_exists = True
                break

        # If this file does not exist we'll need to generate it
        if file_exists is False:
            speech_from_text = gtts.tts.gTTS(
                text=text_to_say,
                lang=language_to_speak
            )
            speech_from_text.save(file_path)

        # Return PyCord-compatible audio source for audio file
        return discord.FFmpegPCMAudio(
            source=file_path,
            options=[["volume", TTS_DEFAULT_VOLUME]]
        )



# Create class instances
tts_file_info_list = TTSFileInfoList(
    file_directory = "tts_cache",
    max_allowed_files = 100
)



# Create TTS slash command group
# TODO: Add checks later, make way for users to use TTS while other audio is
# playing? Seperate TTS bot connection?
tts_slash_command_group = discord.SlashCommandGroup(
    #checks = default,
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



# Define function for letting user say text in voice chat
# TODO: make DM messages that are just text and not slash commands be
# interpretted as TTS
# NOTE: gtts' write_to_fp() theoretically avoids writing to file?
@tts_slash_command_group.command(
    name="play",
    description="Say specified text on your behalf in voice chat.",
    guild_only = False,
    checks=[
        ctx_check.assert_bot_is_in_voice_chat,
        ctx_check.assert_bot_is_in_same_voice_chat_as_author,
        ctx_check.assert_bot_is_not_playing_audio_in_voice_chat,
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
    # TODO: don't hard-code tts name length limit
    tts_user_preference = TTSUserPreference(ctx)
    tts_user_preference.read(ctx.guild.id, ctx.author.id)
    if len(tts_user_preference.spoken_name) > 20:
        err_msg += "\nYour current preferred spoken name, " \
            + "{tts_user_preference.spoken_name}, must be <=20 characters." \
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
    # Get the sound for the text and send it to voice chat

    # Get audio sources
    name_audio_source = tts_file_info_list.get_audio_source(
        text_to_say=tts_user_preference.spoken_name,
        language_to_speak=tts_user_preference.language
    )
    text_audio_source = tts_file_info_list.get_audio_source(
        text_to_say=text_to_say,
        language_to_speak=tts_user_preference.language
    )

    # Play tts_user_preference.spoken_name then text_to_say
    audio_queue.set_next_source(
        voice_client=ctx.bot.voice_clients[0],
        audio_source=text_audio_source,
        after_function=None
    )
    ctx.bot.voice_clients[0].play(
        source=name_audio_source,
        after=audio_queue.play_next_source
    )

    await ctx.respond(
        ephemeral=True,
        content=f"I'm trying to say \"{text_to_say}\"."
    )
    return True



@tts_slash_command_group.command(
    name="spoken_name",
    description="Change the name/pronounciation TTS uses for you in this guild."
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
    if len(new_spoken_name) > 20:
        err_msg += "Please give me a preferred name of <=20 characters."

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
        # TODO: fill in bot owner
        await ctx.respond(
            ephemeral=True,
            content=f"Could not save your new preference for unknown reasons."
                + f"\nPlease tell the bot owner, " \
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
    description="Change the language/accent TTS speaks for you in this guild."
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
        # TODO: fill in bot owner
        await ctx.respond(
            ephemeral=True,
            content=f"Could not save your new preference for unknown reasons."
                + f"\nPlease tell the bot owner, " \
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
