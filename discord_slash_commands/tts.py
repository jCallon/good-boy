# ======================= #
# Import public libraries #
# ======================= #

# General discord API
import discord

# API for using Google to turn text into speech
import gtts

# Operating system API for handling things like moving files
import os

# API for text in a collision-resistant way
import hashlib, binascii

# Custom class for interfacing with JSON files
import discord_slash_commands.helpers.json_list as json_list

# Custom functions for denying commands based off of bot state
import discord_slash_commands.helpers.application_context_checks as application_context_checks

# =========================== #
# Define underlying structure #
# =========================== #

# Define an instance of information held on a user for TTS
class TTSUserPreference(json_list.JSONListItem):
    def __init__(
        self,
        guild_id: int = 0,
        user_id: int = 0,
        spoken_name: str = "",
        language: str = ""
    ):
        # The unique identifier for the guild the user is setting their preferences in, lets users have per-guild settings, ex. 21897521
        self.guild_id = guild_id
        # The unique identifier for the user whose preferences are being defined below, ex. 56918762
        self.user_id = user_id
        # The name the user prefers is spoken when referring to them, useful for names with emojis or that are pronounced odd, ex. Lover = <3er
        self.spoken_name = spoken_name
        # The IETF code of the language the user prefers their TTS to speak in, ex. en = English
        self.language = language

    # Return whether this instance of TTSUserInfo has matching members with comparison_tts_user_preference
    def equals(self, comparison_tts_user_preference) -> bool:
        return (self.guild_id == comparison_tts_user_preference.guild_id) and \
        (self.user_id == comparison_tts_user_preference.user_id) and \
        (self.spoken_name == comparison_tts_user_preference.spoken_name) and \
        (self.language == comparison_tts_user_preference.language)

    # Return a copy of this TTSUserPreference
    def copy(self):
        return TTSUserPreference(self.guild_id, self.user_id, self.spoken_name, self.language)

    # Convert member variables into to dictionary (which are JSON-compatible)
    def to_dict(self) -> dict:
        return {
            "gid": self.guild_id,
            "uid": self.user_id,
            "name": self.spoken_name,
            "lang": self.language
        }

    # Read member varaibles from JSON-compatible dictionary
    def from_dict(self, dictionary: dict) -> None:
        self.guild_id = dictionary["gid"]
        self.user_id = dictionary["uid"]
        self.spoken_name = dictionary["name"]
        self.language = dictionary["lang"]



# Define a list of information held on all users for TTS
class TTSUserPreferenceBank(json_list.JSONList):
    # Get a (a copy of the) user's TTS preferences if they have any
    def get_tts_user_preference(self, member: discord.Member) -> TTSUserPreference:
        # Get the latest file updates
        self.sync()

        # If the user has specified their preference, find it and return a copy (not a reference)
        search_function = lambda tts_user_preference, args: tts_user_preference.guild_id == args[0] and tts_user_preference.user_id == args[1]
        match_index = self.get_list_item_index(search_function, [member.guild.id, member.id])
        if match_index >= 0:
            return self.list[match_index].copy()

        # This user has not specified their preference, return default preferences
        return TTSUserPreference(member.guild.id, member.id, member.display_name, 'en')

    # Add or modify user's TTS preferences
    def add_tts_user_preference(self, new_tts_user_preference: TTSUserPreference) -> bool:
        # Get the latest file updates
        self.sync()

        # If the user had any previous preference, remove it, unless it matches the new preference
        search_function = lambda tts_user_preference, args: tts_user_preference.guild_id == args[0] and tts_user_preference.user_id == args[1]
        match_index = self.get_list_item_index(search_function, [new_tts_user_preference.guild_id, new_tts_user_preference.user_id])
        if match_index >= 0:
            if self.list[match_index].equals(new_tts_user_preference):
                return False
            self.list.pop(match_index)

        # Add new user preference
        self.list.append(new_tts_user_preference)
        self.write()
        return True



# Define what file information we care about when saving audio files for TTS
class TTSFileInfo():
    def __init__(self, file_name: str = "", last_access_time: int = 0):
        # The name of an MP3 file holding TTS, see TTSFileInfoList.get_file_name to see how they're generated
        self.file_name = file_name
        # The time self.file_name was last accessed (this may not be the same as when it was last made or modified)
        self.last_access_time = last_access_time



# Define an API for making PyCord-compatible audio sources for given text and language while keeping your computer clean
class TTSFileInfoList():
    def __init__(self, file_directory: str, max_allowed_files: int):
        # The directory audio generated from text for TTS will be saved
        self.file_directory = file_directory
        # The max number of files allowed to be stored in self.file_directory
        self.max_allowed_files = max_allowed_files

    # Generate a file name to store TTS audio at based on what is being said and what language it is being said in
    # Used: https://cryptobook.nakov.com/cryptographic-hash-functions
    # Use collision-resistant hash to not store plain text from arbitrary plaintext from an unknown source,
    # (hello embedded bash commands!) while also being able to identify if this file has been generated before
    def get_file_name(self, text_to_say: str, language_to_speak: str) -> str:
        byte_array = language_to_speak + text_to_say
        byte_array = byte_array.encode()
        return f"{binascii.hexlify(hashlib.sha3_256(byte_array).digest())}.mp3"

    # Generate a relative file path given a file name
    def get_file_path(self, file_name: str) -> str:
        return f"{self.file_directory}/{file_name}"

    # Create new or give back PyCord audio source for the given text_to_say and language_to_speak
    def get_audio_source(self, text_to_say: str, language_to_speak: str) -> discord.FFmpegPCMAudio: 
        # Get the latest changes
        sorted_list_of_file_info = []
        for file_name in os.listdir(self.file_directory):
            sorted_list_of_file_info.append(TTSFileInfo(file_name, os.stat(self.get_file_path(file_name)).st_atime))
        sorted_list_of_file_info = sorted(sorted_list_of_file_info, key=lambda file_info: file_info.last_access_time)

        # Remove files once over self.max_allowed_files, removing the least recently accessed files
        while len(sorted_list_of_file_info) >= self.max_allowed_files:
            os.path.remove(self.get_file_path(sorted_list_of_file_info[0].file_name))
            sorted_list_of_file_info.pop(0)

        # Generate the file name and path
        file_name = self.get_file_name(text_to_say, language_to_speak)
        file_path = self.get_file_path(file_name)

        # See if there is already an audio file generated for this text_to_say and language_to_speak
        file_exists = False
        for i in range(len(sorted_list_of_file_info)):
            if file_name == sorted_list_of_file_info[i].file_name:
                file_exists = True
                break

        # If this file does not exist we'll need to generate it
        if file_exists == False:
            speech_from_text = gtts.tts.gTTS(text=text_to_say, lang=language_to_speak)
            speech_from_text.save(file_path)

        # Return PyCord-compliant audio source for file
        return discord.FFmpegPCMAudio(source=file_path, options=[["volume", tts_default_volume]]) 
        


# Create class instances
tts_user_preference_instance = TTSUserPreference()
tts_user_preference_bank = TTSUserPreferenceBank(
    file_directory = "json",
    file_name = "tts_user_preference_bank.json",
    list_type_instance = tts_user_preference_instance,
    #max_file_size_in_bytes = default
)
tts_file_info_list = TTSFileInfoList(
    file_directory = "tts_cache",
    max_allowed_files = 100
)



# Create slash command group
# TODO: make way for users to use TTS while other audio is playing? Seperate TTS bot connection?
tts_slash_command_group = discord.SlashCommandGroup(
    checks = [application_context_checks.assert_author_is_allowed_to_call_command],
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



# Create an ad-hoc way to queue audio one-after-another
# TODO: make real audio queue, this pains me
# Set default TTS volume, ex. 2 = 200%
tts_default_volume = 2.0
global next_voice_client
global next_audio_source
global next_after_function
def set_next_audio_queue_source(voice_client, audio_source, after_function):
    global next_voice_client
    global next_audio_source
    global next_after_function
    next_voice_client = voice_client
    next_audio_source = audio_source
    next_after_function = after_function
def play_next_audio_queue_source(error):
    next_voice_client.play(next_audio_source, after=next_after_function)



# Define function for letting user say text in voice chat
# TODO: make DM messages that are just text and not slash commands be interpretted as TTS
# NOTE: gtts' write_to_fp() theoretically avoids writing to file?
@tts_slash_command_group.command(
    name="play",
    description="Say specified text on your behalf in voice chat.",
    guild_only = False,
    checks=[
        application_context_checks.assert_bot_is_in_voice_chat,
        application_context_checks.assert_bot_is_in_same_voice_chat_as_author,
        application_context_checks.assert_bot_is_not_playing_audio_in_voice_chat,
    ]
)
async def tts_play(
    ctx,
    text_to_say: discord.Option(str, description="The text you want said on your behalf in voice chat.")
):
    # TODO: make sure use can't get around blacklist by using DMs

    # Determine if the arguments are valid
    error_message = ""
    if len(text_to_say) == 0:
        error_message += f"\nPlease give me more than 0 characters to say."
    if len(text_to_say) > 500:
        error_message += f"\nPlease break up your text into segments of 500 characters or smaller."

    # If the user's arguments weren't valid, give them verbose error messages and an example to help them
    if error_message != "":
        error_message += f"\nHere's an example command."
        error_message += f"\nGreet everyone in the voice chat the bot is currently connected to."
        error_message += f"\n`/tts play text_to_say: Hi everyone!`"
        await ctx.respond(ephemeral=True, content=error_message)
        return False

    # Determine if user TTS preferences are valid
    # TODO: don't hard-code tts name length limit
    tts_user_preference = tts_user_preference_bank.get_tts_user_preference(ctx.author)
    if len(tts_user_preference.spoken_name) > 20:
        error_message += f"\nYour current preferred spoken name, {tts_user_preference.spoken_name}, exceeds the max of 20 characters. Please change it."
    if tts_user_preference.language not in gtts.lang.tts_langs():
        error_message += f"\nYour TTS language, {tts_user_preference.language}, is not supported anymore. Please change it."

    # If the bot state wasn't valid, give the user verbose error messages to help them
    if error_message != "":
        await ctx.respond(ephemeral=True, content=error_message)
        return False

    # If we got here, the arguments and bot state should be valid and safe to act upon
    # Get the sound for the text and send it to voice chat

    # Get audio sources
    name_audio_source = tts_file_info_list.get_audio_source(text_to_say=tts_user_preference.spoken_name, language_to_speak=tts_user_preference.language)
    text_audio_source = tts_file_info_list.get_audio_source(text_to_say=text_to_say, language_to_speak=tts_user_preference.language)

    # Play tts_user_preference.spoken_name then text_to_say
    # Feels bad, can't pass arguments to the after function, or await the play function, so using globals
    set_next_audio_queue_source(voice_client=ctx.bot.voice_clients[0], audio_source=text_audio_source, after_function=None)
    ctx.bot.voice_clients[0].play(source=name_audio_source, after=play_next_audio_queue_source)

    await ctx.respond(ephemeral=True, content=f"I'm trying to say \"{text_to_say}\".")
    return True



# Define function for letting user change their preferred spoken name used by TTS
@tts_slash_command_group.command(
    name="spoken_name",
    description="Change the name/pronounciation TTS refers to you by."
)
async def tts_spoken_name(
    ctx,
    new_spoken_name: discord.Option(str, description="The name you want to be referred by this bot in voice chat when using TTS.")
):
    # Determine if the arguments are valid
    error_message = ""
    if len(new_spoken_name) == 0:
        error_message += f"Please give me more than 0 characters for your preferred name."
    if len(new_spoken_name) > 20:
        error_message += f"Please give me a preferred name of 20 characters or less."

    # If the user's arguments weren't valid, give them verbose error messages and an example to help them
    if error_message != "":
        error_message += f"\nHere's an example command."
        error_message += f"\nHave TTS call me Pancake Monster."
        error_message += f"\n`/tts spoken_name new_spoken_name: Pancake Monster`"
        await ctx.respond(ephemeral=True, content=error_message)
        return False

    # If we got here, the arguments are valid and safe to act upon
    tts_user_preference = tts_user_preference_bank.get_tts_user_preference(ctx.author)
    tts_user_preference.spoken_name = new_spoken_name
    if tts_user_preference_bank.add_tts_user_preference(tts_user_preference) == False:
        await ctx.respond(ephemeral=True, content=f"Your preferred name for TTS is already {new_spoken_name}.")
        return False
    await ctx.respond(ephemeral=False, content=f"Your preferred name for TTS has been changed to {new_spoken_name}.")
    return True



# Define function for letting user change their language used by TTS
@tts_slash_command_group.command(
    name="language",
    description="Change the language/accent TTS speaks in for you."
)
async def tts_language(
    ctx,
    new_language: discord.Option(str, description="The language (and/or accent) of the text you want spoken when using TTS.")
):
    # Determine if the arguments are valid
    error_message = ""
    if new_language not in gtts.lang.tts_langs():
        error_message += f"I do not know {new_language}."
        error_message += f"\nI use IETF language tags to remember and distinguish between languages. For example, English = `en`."
        error_message += f"\nPlease try to find the tag for your language from this list, if it's not present in this list I don't support it: `"
        for lang in gtts.lang.tts_langs():
            error_message += f"{lang} "
        error_message += f"`\nLearn more at `https://en.wikipedia.org/wiki/IETF_language_tag`."

    # If the user's arguments weren't valid, give them verbose error messages and an example to help them
    if error_message != "":
        error_message += f"\nHere's an example command."
        error_message += f"\nHave TTS use English as my language."
        error_message += f"\n`/tts language new_language: en`"
        await ctx.respond(ephemeral=True, content=error_message)
        return False

    # If we got here, the arguments are valid and safe to act upon
    tts_user_preference = tts_user_preference_bank.get_tts_user_preference(ctx.author)
    tts_user_preference.language = new_language
    if tts_user_preference_bank.add_tts_user_preference(tts_user_preference) == False:
        await ctx.respond(emphemeral=True, content=f"Your language for TTS is already {new_language}.")
        return False
    await ctx.respond(ephemeral=True, content=f"Your language for TTS has been changed to {new_language}.")
    return True
