"""PyCord Discord bot main API.

This file adds all desired individually written PyCord.SlashCommands, found in
the discord_slash_commands directory, to the Discord-accessible bot.
"""

#==============================================================================#
# Import libraries                                                             #
#==============================================================================#

# Import Discord Python API
import discord

# Import operating system module
import os

# Import function for loading environment variables
from dotenv import load_dotenv

#==============================================================================#
# Define underlying structure                                                  #
#==============================================================================#

# Declare PyCord Discord bot, the interface between Discord and the bot code
discord_bot = discord.Bot()



# Add all desired, individually written PyCord.SlashCommand, to the bot
import discord_slash_commands
from discord_slash_commands import rng
discord_bot.add_application_command(rng.rng_slash_command_group)
from discord_slash_commands import voice
discord_bot.add_application_command(voice.voice_slash_command_group)
from discord_slash_commands import tts
discord_bot.add_application_command(tts.tts_slash_command_group)



# Declare event to let bot owner know when the bot is connected to Discord
@discord_bot.event
async def on_ready():
    print(f"{discord_bot.user} is ready and online!")



# Handle event where the bot ran into a run-time error. Some run-time errors
# have a custom payload to tell the message author exactly what they did wrong.
@discord_bot.event
async def on_application_command_error(
    ctx: discord.ApplicationContext,
    error: discord.DiscordException
):
    if isinstance(error, discord.CheckFailure) and \
        isinstance(error.payload, str):
        await ctx.respond(ephemeral=True, content=error.payload)
    else:
        await ctx.respond(ephemeral=True, content="Ran into an unknown error.")
        raise error



#==============================================================================#
# Run Discord bot                                                              #
#==============================================================================#

# Get bot token from environment variables and start bot
load_dotenv()
bot_token = str(os.getenv("TOKEN"))
discord_bot.run(bot_token)
