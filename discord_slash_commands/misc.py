"""TODO.

TODO.
"""

#==============================================================================#
# Import libraries                                                             #
#==============================================================================#

# Import Discord Python API
import discord

# Import functions for asserting bot state
import discord_slash_commands.helpers.application_context_checks as ctx_check

# Import user permissions for each guild
import discord_slash_commands.helpers.user_permission as user_perm

# Import Discord extended APIs to create organized lists
from discord.ext import pages

#==============================================================================#
# Define underlying structure                                                  #
#==============================================================================#

# Define the name of the bot as displayed to others
BOT_NAME = "Silas"

# Create slash command group
bot_slash_command_group = discord.SlashCommandGroup(
    #checks = default,
    #default_member_permissions = default,
    description = "Miscellaneous commands that affect only me",
    #description_localizations = default,
    #guild_ids = default,
    guild_only = True,
    name = BOT_NAME.lower(),
    #name_localizations = default,
    #nsfw = default,
    #parent = default
)

@bot_slash_command_group.command(
    name="kill",
    description="Disconnect me from Discord and stop all my cogs.",
    checks = [ctx_check.assert_author_is_admin]
)
async def bot_kill(ctx):
    """Tell bot to close its connection to Discord and stop all its cogs.

    Tell the bot to close its connection to Discord and stop all of its cogs.
    This effectively kills the bot. The process on the command-line will stop.

    Args:
        ctx: The context this SlashCommand was called under
    """
    # Tell the author to tell the bot owner why they called this command
    await ctx.respond(
        ephemeral = False,
        content = "\nPlease @ the the bot owner, " \
            + f"<@{user_perm.get_bot_owner_discord_user_id()}>, giving " \
            + "a reason for why you've run this command, so they can bug-fix " \
            + "or know what was annoying you." \
            + "\nClosing my connection to Discord now! Goodbye!"
    )

    # Stop all cogs, otherwise they may progress things although the bot is
    # effectively dead, such as thinking they've successfully dispatched
    # certain reminders.
    # Using a for-loop straight on ctx.bot.cogs causes RuntimeError.
    cog_names = ctx.bot.cogs.copy()
    for cog_name in cog_names:
        ctx.bot.remove_cog(cog_name)

    # Close the bot's connection to Discord
    await ctx.bot.close()
    return True
