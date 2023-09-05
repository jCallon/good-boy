# ======================= #
# Import public libraries #
# ======================= #

# General discord API
import discord

# API for using Google to turn text into speech
import gtts

# Custom class for interfacing with JSON files
from discord_slash_commands.helpers.json_list import JSONList

# =========================== #
# Define underlying structure #
# =========================== #

# Define the information held on a user for TTS
class TTSUserPreference:
    def __init__(
        self,
        user_id: int = 0,
        spoken_name: str = "",
        language: str = ""
    ):
        # The unique identifier for the user whose preferences are being defined below
        self.user_id = user_id
        # The name the user prefers is spoken when referring to them, useful for names with emojis or that are pronounced odd
        self.spoken_name = spoken_name
        # The IETF code of the language the user prefers their TTS to speak in, for example, en or es
        self.language = language

    # Convert class to JSON format
    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "spoken_name": self.spoken_name,
            "language": self.language,
        }

    # Read class from JSON format
    def from_dict(self, dictionary: dict) -> None:
        self.user_id = dictionary["user_id"]
        self.spoken_name = dictionary["spoken_name"]
        self.language = dictionary["language"]



# Define the information
class TTSUserPreferenceBank:
    def __init__(
        self,
        file_name: str,
    ):
        # Establish persistent memory (a file to read from and write to)
        self.json_list = JSONList(file_name)
        # Read raw the contents of persisitent memory, parse them into a list of TTSUserPreference
        self.read()

    # If there have been changes to self.json_list, sync with them
    def sync(self) -> bool:
        # If a write has happened since our last read or write...
        if self.json_list.is_desynced():
            # Destroy the old contents of self.tts_user_preference_list and overwrite them with the contents of self.json_list
            self.read()

    # Write the contents of self.tts_user_preference_list to self.json_list
    def write(self) -> list:
        # Create a list of dictionaries to dump into self.json_list
        result = []
        for user in self.tts_user_preference_list:
            result.append(user.to_dict())
        # Dump the list of dictionaries into self.json_list
        self.json_list.write(result)

    # Write the contents of self.json_list to self.tts_user_preference_list
    def read(self) -> None:
        # Clear current user preferences
        self.tts_user_preference_list = []
        # Read and parse the contents of self.json_list
        raw_json_list = self.json_list.read()
        for raw_json_dict in raw_json_list:
            new_entry = TTSUserPreference()
            new_entry.from_dict(raw_json_dict)
            self.tts_user_preference_list.append(new_entry)

    # Get a user's TTS preferences if they have them
    def get_tts_user_preference(self, member: discord.Member) -> TTSUserPreference:
        # Sync with latest changes
        self.sync()

        # If the user has specified their preference, find it and return it
        for tts_user_preference in self.tts_user_preference_list:
            if tts_user_preference.user_id == member.id:
                return tts_user_preference

        # This user has not specified their preference, give them default
        return TTSUserPreference(member.id, member.display_name, 'en')

    # Add or modify user's TTS preferences
    def add_tts_user_preference(self, new_tts_user_preference: TTSUserPreference) -> bool:
        # Sync with latest changes
        self.sync()

        # If the user had previous preference, remove it, unless it matches the new preference
        for i in range(len(self.tts_user_preference_list)):
            if self.tts_user_preference_list[i].user_id == new_tts_user_preference.user_id:
                if self.tts_user_preference_list[i] == new_tts_user_preference:
                    return False
                self.tts_user_preference_list.pop(i)

        # Add new user preference
        self.tts_user_preference_list.append(new_tts_user_preference)
        self.write()



# Create instance of TTSUserPreferenceBank
tts_user_preference_bank = TTSUserPreferenceBank("tts")



# Create slash command group
tts_slash_command_group = discord.SlashCommandGroup("tts", "Text to speech commands")



# Define function for letting user say text in voice chat
@tts_slash_command_group.command(name="play", description="Say some text in voice chat.")
async def tts_play(
    ctx,
    text_to_say: discord.Option(str, decription="The text you want said on your behalf in voice chat.")
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

    # Determine if the bot state is valid
    if len(bot.voice_clients) == 0:
        error_message += f"\nI am not in a voice chat. Please connect me to a voice channel to speak in via \\voice join."
    if len(bot.voice_clients > 0) and bot.voice_clients[0].is_playing():
        error_message += f"\nI am already playing audio. Please wait until I finish playing my current audio, or stop it via \\voice stop."
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
    # TODO
    await ctx.respond("This has not been implemented.")
    return True


# Define function for letting user change their preferred spoken name used by TTS
@tts_slash_command_group.command(name="spoken_name", description="Change the name TTS will refer to you by. Useful for correcting pronounciation.")
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
@tts_slash_command_group.command(name="language", description="Change the language you want your text to be interpretted in using TTS.")
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
