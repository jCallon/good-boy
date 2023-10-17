# ======================= #
# Import public libraries #
# ======================= #

# Import Discord Python API
import discord

# Import operating system module
import os

# Import module for loading environment variables
from dotenv import load_dotenv

# =========================== #
# Define underlying structure #
# =========================== #

# Enable accurate member cache (needed for settings slash commands)
discord.Intents.default().members = True

# Load environment variables
load_dotenv()

# Declare Discord bot
discord_bot = discord.Bot()

# Declare events for Discord bot
@discord_bot.event
async def on_ready():
    print(f"{discord_bot.user} is ready and online!")

# Import commands for Discord bot
import discord_slash_commands
from discord_slash_commands import rng as rng_slash_commands
discord_bot.add_application_command(rng_slash_commands.rng_slash_command_group)
from discord_slash_commands import voice as voice_slash_commands
discord_bot.add_application_command(voice_slash_commands.voice_slash_command_group)
from discord_slash_commands import tts as tts_slash_commands
discord_bot.add_application_command(tts_slash_commands.tts_slash_command_group)
from discord_slash_commands import settings as settings_slash_commands
discord_bot.add_application_command(settings_slash_commands.settings_slash_command_group)

@discord_bot.event
async def on_application_command_error(ctx: discord.ApplicationContext, error: discord.DiscordException):
    if isinstance(error, discord.CheckFailure) and isinstance(error.payload, str):
        await ctx.respond(ephemeral=True, content=error.payload)
    else:
        await ctx.respond(ephemeral=True, content="Ran into an unknown error.")
        raise error

# =============== #
# Run Discord bot #
# =============== #

bot_token = str(os.getenv("TOKEN"))
discord_bot.run(bot_token)
