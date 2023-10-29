"""PyCord Discord bot main API.

This file adds all desired individually written PyCord.SlashCommands, found in
the discord_slash_commands directory, to the Discord-accessible bot.
"""

#==============================================================================#
# Import libraries                                                             #
#==============================================================================#

# Import operating system module
import os

# Import Discord Python API
import discord

# Import function for loading environment variables
from dotenv import load_dotenv

# Import all PyCord.SlashCommand desired to be added to the to the bot
from discord_slash_commands import rng
from discord_slash_commands import voice
from discord_slash_commands import tts

# Import SQL helper for persistent, mmulti-thread safe bot memory
from discord_slash_commands.helpers import sql

#==============================================================================#
# Define underlying structure                                                  #
#==============================================================================#

# Declare PyCord Discord bot, the interface between Discord and the bot code,
# and add all PyCord.SlashCommand desired to be added to the to the bot
discord_bot = discord.Bot()
discord_bot.add_application_command(rng.rng_slash_command_group)
discord_bot.add_application_command(voice.voice_slash_command_group)
discord_bot.add_application_command(tts.tts_slash_command_group)



@discord_bot.event
async def on_ready():
    """Handles on_ready event for discord_bot.

    Initializes connections to necessary internal databases and prints a string
    in-console to let the bot owner know when the bot has connected to Discord.
    """
    # Create or get connection to existing TTS information database
    # TODO: Do connections need to be closed before the application closes?
    sql.add_conection(
        table_name="tts_info",
        column_name_list=[
            "guild_id",
            "user_id",
            "spoken_name",
            "language"
        ]
    )

    # TODO: uncomment once feature is enabled
    # Create or get connection to existing member permissions database
    #sql.add_conection(
    #    table_name="permissions",
    #    column_name_list=[
    #        "guild_id",
    #        "user_id",
    #        "is_admin",
    #        "is_blacklisted"
    #    ]
    #)

    # TODO: uncomment once feature is enabled
    # Create or get connection to existing polls database
    #sql.add_connection(
    #    table_name="polls",
    #    column_name_list=[
    #        "message_id",
    #        "expiration"
    #    ]
    #)

    # TODO: uncomment once feature is enabled
    # Create or get connection to existing reminders database
    #sql.add_connection(
    #    table_name="reminders",
    #    column_name_list=[
    #        "author_user_id",
    #        "channel id",
    #        "recurrance_type",
    #        "start",
    #        "end", 
    #        "content"
    #    ]
    #)

    # Print string in console to let bot owner know bot is connected to Discord
    # and ready to run commands
    print(f"{discord_bot.user} is ready and online!")

@discord_bot.event
async def on_application_command_error(
    ctx: discord.ApplicationContext,
    error: discord.DiscordException
):
    """Handles the on_application_command_error event for discord_bot.

    Tell the message author a run-time error was raised. If there was a custom
    payload attached to the error, to tell the message author exactly why the
    error occured and how to fix it, tell them that that instead.

    Args:
        ctx: Context information for the flow the error happened from
        error: The error raised during execution of the author's message
    """
    # Check if error has custom payload to deliver to the message author
    if isinstance(error, discord.CheckFailure) and \
        isinstance(error.payload, str):
        # Deliver error payload to message author
        await ctx.respond(ephemeral=True, content=error.payload)
        return

    # Otherwise, just tell the message author there was a error,
    # we don't know more than that and might not want to say more than that
    await ctx.respond(ephemeral=True, content="Ran into an unknown error.")

    # Elevate error so bot-owner sees it in-console
    raise error

@discord_bot.event
async def on_application_command_error(
    ctx: discord.ApplicationContext,
    error: discord.DiscordException
):


#==============================================================================#
# Run Discord bot                                                              #
#==============================================================================#

# Load environment variables
load_dotenv()
# Get bot token from environment variables
BOT_TOKEN = str(os.getenv("TOKEN"))
# Start bot
discord_bot.run(BOT_TOKEN)
