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
from discord_slash_commands import permissions
from discord_slash_commands import reminder

# Import helper for interacting with internal database
from discord_slash_commands.helpers import sqlite

#==============================================================================#
# Define underlying structure                                                  #
#==============================================================================#

# Enable accurate member cache (needed for settings slash commands)
discord.Intents.default().members = True



# Load environment variables
load_dotenv()



# Declare PyCord Discord bot, the interface between Discord and the bot code,
# and add all PyCord.SlashCommand desired to be added to the to the bot
discord_bot = discord.Bot(intents=discord.Intents.default())
discord_bot.add_application_command(rng.rng_slash_command_group)
discord_bot.add_application_command(voice.voice_slash_command_group)
discord_bot.add_application_command(tts.tts_slash_command_group)
discord_bot.add_application_command(permissions.permissions_slash_command_group)
discord_bot.add_application_command(reminder.reminder_slash_command_group)



@discord_bot.event
async def on_ready():
    """Handles on_ready event for discord_bot.

    Initializes connections to necessary internal databases and prints a string
    in-console to let the bot owner know when the bot has connected to Discord.
    """
    connected_guild_id_list = []
    for guild in discord_bot.guilds:
        connected_guild_id_list.append(f"guild_{guild.id}")

    # Create or get connection to existing TTS information database
    # TODO: Do connections need to be closed before the application closes?
    # TODO: Make new tables when connecting to a new guild
    # TODO: Make spoken name unique?
    sqlite.add_connection(
        file_name="tts_info",
        table_name_list=connected_guild_id_list,
        column_list=[
            "user_id INTEGER NOT NULL PRIMARY KEY",
            "spoken_name TEXT NOT NULL",
            "language TEXT NOT NULL"
        ]
    )

    # Create or get connection to existing member permissions database
    sqlite.add_connection(
        file_name="permissions",
        table_name_list=connected_guild_id_list,
        column_list=[
            "user_id INTEGER NOT NULL PRIMARY KEY",
            "is_admin INTEGER NOT NULL",
            "is_blacklisted INTEGER NOT NULL"
        ]
    )

    # TODO: uncomment once feature is enabled
    # Create or get connection to existing polls database
    #sqlite.add_connection(
    #    file_name="polls",
    #    table_name_list=["outstanding_polls"],
    #    column_list=[
    #        "message_id INTEGER NOT NULL PRIMARY KEY",
    #        "expiration INTEGER NOT NULL"
    #    ]
    #)

    # Create or get connection to existing reminders database
    sqlite.add_connection(
        file_name="reminders",
        table_name_list=["outstanding_reminders"],
        column_list=[
            "reminder_id INTEGER NOT NULL PRIMARY KEY",
            "author_user_id INTEGER NOT NULL",
            "channel_id INTEGER NOT NULL",
            "recurrence_type TEXT NOT NULL",
            "next_occurrence_time INTEGER NOT NULL",
            "expiration_time INTEGER NOT NULL",
            "content TEXT"
        ]
    )

    # Print string in console to let bot owner know bot is connected to Discord
    # and ready to run commands
    print(f"{discord_bot.user} is ready and online!")

    # Add cog containing task to dispatch reminders every minute
    discord_bot.add_cog(reminder.ReminderCog(bot=discord_bot))



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



#==============================================================================#
# Run Discord bot                                                              #
#==============================================================================#

# Get bot token from environment variables
BOT_TOKEN = str(os.getenv("TOKEN"))
# Start bot
discord_bot.run(BOT_TOKEN)
