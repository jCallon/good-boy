# ======================= #
# Import public libraries #
# ======================= #

# General discord API
import discord

# API for using Google to turn text into speech
import gtts

# API for creating BytesIO file-like object
import io

# TODO: comment
import random

# Custom class for interfacing with JSON files
import discord_slash_commands.helpers.json_list as json_list

# Custom functions for denying commands based off of bot state
import discord_slash_commands.helpers.application_context_checks as application_context_checks

# =========================== #
# Define underlying structure #
# =========================== #



global after_function_voice_client
global after_function_discord_audio_source
def pain(error):
    global after_function_voice_client
    global after_function_discord_audio_source
    after_function_voice_client.play(after_function_discord_audio_source)



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

    # Return whether this instance of TTSUserInfo has matching members with new_tts_user_preference
    def equals(self, comparison_tts_user_preference) -> bool:
        return (self.guild_id == comparison_tts_user_preference.guild_id) and \
        (self.user_id == comparison_tts_user_preference.user_id) and \
        (self.spoken_name == comparison_tts_user_preference.spoken_name) and \
        (self.language == comparison_tts_user_preference.language)

    # Return a copy of this TTSUserPreference
    def copy(self):
        return TTSUserPreference(self.guild_id, self.user_id, self.spoken_name, self.language)

    # Convert class to JSON format
    def to_dict(self) -> dict:
        return {
            "gid": self.guild_id,
            "uid": self.user_id,
            "name": self.spoken_name,
            "lang": self.language
        }

    # Read class from JSON format
    def from_dict(self, dictionary: dict) -> None:
        self.guild_id = dictionary["gid"]
        self.user_id = dictionary["uid"]
        self.spoken_name = dictionary["name"]
        self.language = dictionary["lang"]



# Define the information
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

        # This user has not specified their preference, give them default
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



# Create instance of TTSUserPreferenceBank
tts_user_preference_instance = TTSUserPreference()
tts_user_preference_bank = TTSUserPreferenceBank("json", "tts_user_preference_bank.json", tts_user_preference_instance)



# Set default TTS volume, ex. 2 = 200%
tts_default_volume = 2.0



# Create slash command group
# TODO: Add checks later, make way for users to use TTS while other audio is playing? Seperate TTS bot connection?
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



# Define function for letting user say text in voice chat
# TODO: make DM messages that are just text and not slash commands be interpretted as TTS
@tts_slash_command_group.command(
    name="play",
    description="Say specified text on your behalf in voice chat.",
    guild_only = False,
    checks=[
        application_context_checks.assert_bot_is_in_voice_chat,
        application_context_checks.assert_bot_is_in_same_voice_chat_as_user,
        application_context_checks.assert_bot_is_not_playing_audio_in_voice_chat,
    ]
)
async def tts_play(
    ctx,
    text_to_say: discord.Option(str, description="The text you want said on your behalf in voice chat.")
):
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
        error_message += f"\n`\\tts play \"Hi everyone!\"`"
        await ctx.respond(error_message)
        return False

    # Determine if user TTS preferences are valid
    tts_user_preference = tts_user_preference_bank.get_tts_user_preference(ctx.author)
    if len(tts_user_preference.spoken_name) > 20:
        error_message += f"\nYour current preferred spoken name, {tts_user_preference.spoken_name}, exceeds the max of 20 characters. Please change it."
    if tts_user_preference.language not in gtts.lang.tts_langs():
        error_message += f"\nYour TTS language, {tts_user_preference.language}, is not supported anymore. Please change it."

    # If the bot state wasn't valid, give the user verbose error messages to help them
    if error_message != "":
        await ctx.respond(error_message)
        return False

    # If we got here, the arguments and bot state should be valid and safe to act upon
    # Get the sound for the text and send it to voice chat

    # TODO: comment, save files as first 10 characters of name/text, if file already exists use it instead of genreating new file
    random_int = random.randint(1, 4294967295)
    name_file_path = f"tmp/{random_int}.mp3"
    text_file_path = f"tmp/{random_int - 1}.mp3"

    # TODO: comment
    speech_from_text = gtts.tts.gTTS(text=tts_user_preference.spoken_name, lang=tts_user_preference.language)
    speech_from_text.save(name_file_path)
    name_discord_ffmpeg_audio_source = discord.FFmpegPCMAudio(source=name_file_path, options=[["volume", tts_default_volume]]) 

    # TODO: comment
    speech_from_text = gtts.tts.gTTS(text=text_to_say, lang=tts_user_preference.language)
    speech_from_text.save(text_file_path)
    text_discord_ffmpeg_audio_source = discord.FFmpegPCMAudio(source=text_file_path, options=[["volume", tts_default_volume]]) 

    # Feels bad, can't pass arguments to the after function, or await the play function, so using globals
    global after_function_voice_client
    after_function_voice_client = ctx.bot.voice_clients[0]
    global after_function_discord_audio_source
    after_function_discord_audio_source = text_discord_ffmpeg_audio_source
    ctx.bot.voice_clients[0].play(source=name_discord_ffmpeg_audio_source, after=pain)

    # Delete file if there are over 100

    # Generate volume-controlled audio for tts_user_preference.spoken_name
    # TODO find a way to use write_to_fp() to avoid writing to file, save user's name instead of regenerating
    #mp3_file_like_object = io.BytesIO()
    #speech_from_text = gtts.tts.gTTS(text=tts_user_preference.spoken_name, lang=tts_user_preference.language)
    #speech_from_text.write_to_fp(mp3_file_like_object)
    #spoken_name_discord_ffmpeg_audio_source = discord.FFmpegPCMAudio(source=sad, options=[["volume", tts_default_volume]])
    #sad = io.BufferedIOBase()
    #sad.raw = mp3_file_like_object.getbuffer()
    #sad.read = mp3_file_like_object.read1
    #spoken_name_discord_ffmpeg_audio_source = discord.FFmpegPCMAudio(source=sad, pipe=True, options=[["volume", tts_default_volume]])

    # Generate volume-controlled audio source for text_to_be_spoken
    #mp3_file_like_object = io.BytesIO()
    #speech_from_text = gtts.tts.gTTS(text=text_to_say, lang=tts_user_preference.language)
    #speech_from_text.write_to_fp(mp3_file_like_object)
    #spoken_text_discord_ffmpeg_audio_source = discord.FFmpegPCMAudio(source=mp3_file_like_object, options=[["volume", tts_default_volume]])

    #bot.play(spoken_name_discord_ffmpeg_audio_source, lambda error: bot.play(spoken_text_discord_ffmpeg_audio_source))

    await ctx.respond(f"I'm trying to say \"{text_to_say}\".")
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
        error_message += f"\n`\\tts spoken_name \"Pancake Monster\"`"
        await ctx.respond(error_message)
        return False

    # If we got here, the arguments are valid and safe to act upon
    tts_user_preference = tts_user_preference_bank.get_tts_user_preference(ctx.author)
    tts_user_preference.spoken_name = new_spoken_name
    if tts_user_preference_bank.add_tts_user_preference(tts_user_preference) == False:
        await ctx.respond(f"Your preferred name for TTS is already {new_spoken_name}.")
        return False
    await ctx.respond(f"Your preferred name for TTS has been changed to {new_spoken_name}.")
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
        error_message += f"\n`\\tts language \"en\"`"
        await ctx.respond(error_message)
        return False

    # If we got here, the arguments are valid and safe to act upon
    tts_user_preference = tts_user_preference_bank.get_tts_user_preference(ctx.author)
    tts_user_preference.language = new_language
    if tts_user_preference_bank.add_tts_user_preference(tts_user_preference) == False:
        await ctx.respond(f"Your language for TTS is already {new_language}.")
        return False
    await ctx.respond(f"Your language for TTS has been changed to {new_language}.")
    return True
