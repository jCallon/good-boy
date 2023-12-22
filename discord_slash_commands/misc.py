"""PyCord.SlashCommand for miscellaneous activities.

This file defines slash commands that might not fit in with other slash command
groups. For example, killing the bot, which doesn't have to do with voice, tts,
or permissions.
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

#==============================================================================#
# Define underlying structure                                                  #
#==============================================================================#

# Define some useful constants to avoid copy/paste
BOT_NAME = "Silas"
BOT_REPO = "https://github.com/jCallon/good-boy"



# Create slash command group
bot_slash_command_group = discord.SlashCommandGroup(
    #checks = default,
    #default_member_permissions = default,
    description = f"Miscellaneous commands that affect only me, {BOT_NAME}",
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
    description="Tell me to stop running.",
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
    # (Using a for-loop straight on ctx.bot.cogs causes a RuntimeError.)
    cog_names = ctx.bot.cogs.copy()
    for cog_name in cog_names:
        ctx.bot.remove_cog(cog_name)

    # Close the bot's connection to Discord
    await ctx.bot.close()
    return True



@bot_slash_command_group.command(
    name="help",
    description="Give you more details about me.",
    checks = [ctx_check.assert_author_is_admin]
)
async def bot_help(ctx):
    """Tell bot give you more information on it.

    Tell the bot to give you more information on it, so you may, for example,
    see the bot code, command overview, and suggest bug-fixes/improvements.

    Args:
        ctx: The context this SlashCommand was called under
    """
    # Give author a bunch of helpful links that should have up-to-date info
    await ctx.respond(
        ephemeral = True,
        content = f"My owner: <@{user_perm.get_bot_owner_discord_user_id()}>." \
            + f"\nAdd/see issues and suggestions: {BOT_REPO}/issues" \
            + f"\nSee my command overview: {BOT_REPO}/blob/main/README.md" \
            + f"\nSee my code: {BOT_REPO}" \
            + "\nYou may make, modify, and dispatch your own copy of my code " \
            + "without anyone's permission. But, to contribute your own " \
            + "changes to the repo, please make a PR and contact the repo " \
            + "owner for review. If you don't know what that means, but " \
            + "still want to help, just email whoever is committing the most."
    )
    return True
