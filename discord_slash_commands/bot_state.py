# ======================= #
# Import public libraries #
# ======================= #

# General discord API
import discord

# Custom classes for keeping track of user's permissions for this bot
import discord_slash_commands.helpers.permissions as permissions

# Custom functions for denying commands based off of bot state
import discord_slash_commands.helpers.application_context_checks as application_context_checks

# =========================== #
# Define underlying structure #
# =========================== #

# Create slash command group
bot_state_slash_command_group = discord.SlashCommandGroup(
    checks = [application_context_checks.assert_author_is_admin],
    #default_member_permissions = default,
    description="Commands that affect the state of this bot",
    #description_localizations = default,
    #guild_ids = default,
    guild_only = True,
    name = "bot_state",
    #name_localizations = default,
    #nsfw = default,
    #parent = default
)

#TODO: rename from bot_state to settings?



# Define function for letting admin blacklist users from using bot
@bot_state_slash_command_group.command(
    name="blacklist",
    description="Ban someone (ex. annoying/abusive) from using me."
)
async def bot_state_blacklist(
    ctx,
    name_of_member_to_blacklist: discord.Option(int, description="The name of the member you want to blacklist."),
    reason_for_blacklisting_member: discord.Option(str, description="The reason you are blacklisting this member.")
):
    # Determine if the arguments are valid
    error_message = ""
    member_to_blacklist = ctx.guild.get_member_named(name_of_member_to_blacklist)
    if member_to_blacklist == None:
        error_message += f"\nI could not find a member in this guild named {name_of_member_to_blacklist}."
    if permissions.user_has_permission("admin", member_to_blacklist.id, ctx.guild.id):
        error_message += f"\nYou cannot blacklist other admins. Please ask the bot owner to un-admin the offending admin."
    if len(reason_for_blacklisting_member) < 1:
        error_message += f"\nPlease give a reason you are blacklisting this member (it will be visible to all unless deleted for record-keeping)."

    # If the user's arguments weren't valid, give them verbose error messages and an example to help them
    if error_message != "":
        error_message += f"\nHere's an example command."
        error_message += f"\nBan Sell Sell $ell! from using this bot because they use it make unsolicited advertisements."
        error_message += f"\n`/admin blacklist name_of_member_to_blacklist: Sell Sell $ell! "
        error_message += f"reason_for_blacklisting_member: Used the bot for spamming users with advertisements of their merchandise."
        await ctx.respond(ephemeral=True, content=error_message)
        return False

        # If we got here, the arguments are valid and safe to act upon
        # Try to add this user to the list of blacklisted users for this guild
        if permission.modify_user_permission("blacklisted", "add", member_to_blacklist.id, ctx.guild.id) == False:
            await ctx.respond(ephemeral=True, content=f"{name_of_member_to_blacklist} is already blacklisted in this guild.")
            return False

        await ctx.respond(ephemeral=False, content=f"Blacklisted {name_of_member_to_blacklist} in this guild.")
        return True



# Define function for letting admin unblacklist users from using bot
@bot_state_slash_command_group.command(name="unblacklist", description="Unban someone previously banned from using me.")
async def bot_state_unblacklist(
    ctx,
    name_of_member_to_unblacklist: discord.Option(int, description="The name of the member you want to blacklist.")
):
    # Determine if the arguments are valid
    error_message = ""
    member_to_unblacklist = ctx.guild.get_member_named(member_name)
    if member_to_unblacklist == None:
        error_message += f"\nI could not find a member in this guild named {name_of_member_to_unblacklist}."

    # If the user's arguments weren't valid, give them verbose error messages and an example to help them
    if error_message != "":
        error_message += f"\nHere's an example command."
        error_message += f"\nUnban Sell Sell $ell! from using this bot. They have made ammends."
        error_message += f"\n`/admin unblacklist name_of_member_to_unblacklist: Sell Sell $ell!`"
        await ctx.respond(ephemeral=True, content=error_message)
        return False

    # If we got here, the arguments are valid and safe to act upon
    # Try to remove this user from the list of blacklisted users for this guild
    if permission.modify_user_permission("blacklisted", "remove", member_to_unblacklist.id, ctx.guild.id) == False:
        await ctx.respond(ephemeral=True, content=f"{name_of_member_to_blacklist} is already blacklisted in this guild.")
        return False

    await ctx.respond(ephemeral=False, content=f"Blacklisted {name_of_member_to_blacklist} in this guild.")
    return True



# Define function for letting bot owner add bot admins
@bot_state_slash_command_group.command(
    name="admin",
    description="Trust a member as one of my admins in this guild.",
    checks=[application_context_checks.assert_author_is_bot_owner]
)
async def bot_state_add(
    ctx,
    name_of_member_to_admin: discord.Option(int, description="The name of the member you want to admin.")
):
    # Determine if the arguments are valid
    error_message = ""
    member_to_admin = ctx.guild.get_member_named(name_of_member_to_admin)
    if member_to_admin == None:
        error_message += f"\nI could not find a member in this guild named {name_of_member_to_admin}."

    # If the user's arguments weren't valid, give them verbose error messages and an example to help them
    if error_message != "":
        error_message += f"\nHere's an example command."
        error_message += f"\nAdd Xx_L33T.guild.ADMIN_xX as a bot admin for me."
        error_message += f"\n`/bot_state admin name_of_member_to_admin: Xx_L33T.guild.ADMIN_xX`"
        await ctx.respond(ephemeral=True, content=error_message)
        return False

    # If we got here, the arguments are valid and safe to act upon
    if permission.modify_user_permission("admin", "add", member_to_admin.id, ctx.guild.id) == False:
        await ctx.respond(ephemeral=True, content=f"{name_of_member_to_admin} is already a bot admin in this guild.")
        return False

    await ctx.respond(ephemeral=False, content=f"Promoted {name_of_member_to_admin} to bot admin in this guild.")
    return True

# Define function for letting bot owner remove bot admins
@bot_state_slash_command_group.command(
    name="unadmin",
    description="Untrust a member as one of my admins in this guild.",
    checks=[application_context_checks.assert_author_is_bot_owner]
)
async def bot_state_remove(
    ctx,
    member_name: discord.Option(int, description="The name of the member you want to blacklist.")
):
    # Determine if the arguments are valid
    error_message = ""
    member_to_unadmin = ctx.guild.get_member_named(name_of_member_to_unadmin)
    if member_to_unadmin == None:
        error_message += f"\nI could not find a member in this guild named {name_of_member_to_unadmin}."

    # If the user's arguments weren't valid, give them verbose error messages and an example to help them
    if error_message != "":
        error_message += f"\nHere's an example command."
        error_message += f"\nRemove Xx_L33T.guild.ADMIN_xX as a bot admin for me."
        error_message += f"\n`/bot_state unadmin name_of_member_to_unadmin: Xx_L33T.guild.ADMIN_xX`"
        await ctx.respond(ephemeral=True, content=error_message)
        return False

    # If we got here, the arguments are valid and safe to act upon
    if permission.modify_user_permission("admin", "remove", member_to_unadmin.id, ctx.guild.id) == False:
        await ctx.respond(ephemeral=True, content=f"{name_of_member_to_unadmin} is already a bot admin in this guild.")
        return False

    await ctx.respond(ephemeral=False, content=f"Promoted {name_of_member_to_admin} to bot admin in this guild.")
    return True



# Define function for letting admin pause bot
@bot_state_slash_command_group.command(
    name="pause",
    description="Make me unresponsive to non-admin commands.",
    checks=[application_context_checks.assert_bot_is_accepting_non_admin_commands]
)
async def bot_state_pause(ctx):
    application_context_checks.bot_is_accepting_non_admin_commands = False
    await ctx.respond(ephemeral=False, content=f"I will no longer accept non-admin commands until the next `/bot_state unpause`.")
    return True



# Define function for letting admin unpause bot
@bot_state_slash_command_group.command(
    name="unpause",
    description="Make me responsive to non-admin messages.",
    checks=[application_context_checks.assert_bot_is_not_accepting_non_admin_commands]
)
async def bot_state_unpause(ctx):
    application_context_checks.bot_is_accepting_non_admin_commands = True
    await ctx.respond(ephemeral=False, content=f"I will accept non-admin commands until the next `/bot_state pause`.")
    return True



# Define function for letting admin kill bot
@bot_state_slash_command_group.command(
    name="kill",
    description="Kill this bot instance for all guilds."
)
async def bot_state_kill(ctx):
    await ctx.respond(ephemeral=False, content=f"Farewell. May I open my eyes again, or may my sleep be forever peaceful.")
    await ctx.bot.close()
    return True
