# ======================= #
# Import public libraries #
# ======================= #

# General discord API
import discord

# Get user permissions in this guild
from discord_slash_commands.helpers.guild_permission import guild_permission_bank

# Custom functions for denying commands based off of bot state
import discord_slash_commands.helpers.application_context_checks as application_context_checks

# =========================== #
# Define underlying structure #
# =========================== #

# Create slash command group
settings_slash_command_group = discord.SlashCommandGroup(
    checks = [application_context_checks.assert_author_is_admin],
    #default_member_permissions = default,
    description="Commands that affect the state of this bot",
    #description_localizations = default,
    #guild_ids = default,
    guild_only = True,
    name = "settings",
    #name_localizations = default,
    #nsfw = default,
    #parent = default
)



#############
# Blacklist #
#############



# Create slash command sub-group
blacklist_slash_command_group = settings_slash_command_group.create_subgroup(
    name = "blacklist",
    description="Commands that affect whether a certain individual can use the bot",
    #guild_ids = default,
    guild_only = True,
    #nsfw = default,
    #default_member_permissions = default,
    #checks = default,
    #name_localizations = default,
    #description_localizations = default,
)



# Define function for letting admin blacklist users from using bot
# TODO: store reason?
@blacklist_slash_command_group.command(
    name="add",
    description="Ban someone (ex. annoying/abusive) from using me."
)
async def blacklist_add(
    ctx,
    name_of_member_to_blacklist: discord.Option(str, description="The name of the member you want to blacklist."),
    reason_for_blacklisting_member: discord.Option(str, description="The reason you are blacklisting this member.")
):
    # Determine if the arguments are valid
    error_message = ""
    member_to_blacklist = ctx.guild.get_member_named(name_of_member_to_blacklist)
    if member_to_blacklist == None:
        error_message += f"\nI could not find a member in this guild named {name_of_member_to_blacklist}."
    if member_to_blacklist != None and guild_permission_bank.user_has_permission("admin", member_to_blacklist.id, ctx.guild.id):
        error_message += f"\nYou cannot blacklist other admins. Please ask the bot owner to un-admin the offending admin."
    if len(reason_for_blacklisting_member) < 1:
        error_message += f"\nPlease give a reason you are blacklisting this member (it will be visible to all unless deleted for record-keeping)."

    # If the user's arguments weren't valid, give them verbose error messages and an example to help them
    if error_message != "":
        error_message += f"\nHere's an example command."
        error_message += f"\nBan Sell Sell $ell! from using this bot because they use it make unsolicited advertisements."
        error_message += f"\n`/admin blacklist add name_of_member_to_blacklist: Sell Sell $ell! "
        error_message += f"reason_for_blacklisting_member: Used the bot for spamming users with advertisements of their merchandise.`"
        await ctx.respond(ephemeral=True, content=error_message)
        return False

    # If we got here, the arguments are valid and safe to act upon
    # Try to add this user to the list of blacklisted users for this guild
    if guild_permission_bank.modify_user_id_list("blacklisted", "add", member_to_blacklist.id, ctx.guild.id) == False:
        await ctx.respond(ephemeral=True, content=f"{name_of_member_to_blacklist} is already blacklisted in this guild.")
        return False

    await ctx.respond(ephemeral=False, content=f"Blacklisted {name_of_member_to_blacklist} in this guild.")
    return True



# Define function for letting admin unblacklist users from using bot
@blacklist_slash_command_group.command(
    name="remove",
    description="Unban someone previously banned from using me."
)
async def blacklist_remove(
    ctx,
    name_of_member_to_unblacklist: discord.Option(str, description="The name of the member you want to unblacklist.")
):
    # Determine if the arguments are valid
    error_message = ""
    member_to_unblacklist = ctx.guild.get_member_named(name_of_member_to_unblacklist)
    if member_to_unblacklist == None:
        error_message += f"\nI could not find a member in this guild named {name_of_member_to_unblacklist}."

    # If the user's arguments weren't valid, give them verbose error messages and an example to help them
    if error_message != "":
        error_message += f"\nHere's an example command."
        error_message += f"\nUnban Sell Sell $ell! from using this bot. They have made ammends."
        error_message += f"\n`/admin blacklist remove name_of_member_to_unblacklist: Sell Sell $ell!`"
        await ctx.respond(ephemeral=True, content=error_message)
        return False

    # If we got here, the arguments are valid and safe to act upon
    # Try to remove this user from the list of blacklisted users for this guild
    if guild_permission_bank.modify_user_id_list("blacklisted", "remove", member_to_unblacklist.id, ctx.guild.id) == False:
        await ctx.respond(ephemeral=True, content=f"{name_of_member_to_unblacklist} is already not blacklisted in this guild.")
        return False

    await ctx.respond(ephemeral=False, content=f"Unblacklisted {name_of_member_to_unblacklist} in this guild.")
    return True



@blacklist_slash_command_group.command(
    name="list",
    description="See the members blacklisted in this guild."
)
async def blacklist_list(ctx):
    blacklist_user_id_list = guild_permission_bank.get_user_id_list("blacklisted", ctx.guild.id)
    response = ""
    for user_id in blacklist_user_id_list:
        response += f"<@{user_id}>,"
    if response == "":
        await ctx.respond(ephemeral=True, content=f"I have no one blacklisted in this guild.")
    else:
        await ctx.respond(ephemeral=True, content=f"[{response}]")
    return True



#########
# Admin #
#########



# Create slash command sub-group
admin_slash_command_group = settings_slash_command_group.create_subgroup(
    name = "admin",
    description="Commands used to affect who has elevated privelages for this bot",
    #guild_ids = default,
    guild_only = True,
    #nsfw = default,
    #default_member_permissions = default,
    checks=[application_context_checks.assert_author_is_bot_owner]
    #name_localizations = default,
    #description_localizations = default,
)



# Define function for letting bot owner add bot admins
@admin_slash_command_group.command(
    name="add",
    description="Add a member to my list of trusted users in this guild.",
)
async def admin_add(
    ctx,
    name_of_member_to_admin: discord.Option(str, description="The name of the member you want to admin.")
):
    # Determine if the arguments are valid
    error_message = ""
    member_to_admin = ctx.guild.get_member_named(name_of_member_to_admin)
    print(ctx.guild.members)
    if member_to_admin == None:
        error_message += f"\nI could not find a member in this guild named {name_of_member_to_admin}."

    # If the user's arguments weren't valid, give them verbose error messages and an example to help them
    if error_message != "":
        error_message += f"\nHere's an example command."
        error_message += f"\nAdd Xx_L33T.guild.ADMIN_xX as a bot admin for me."
        error_message += f"\n`/settings admin add name_of_member_to_admin: Xx_L33T.guild.ADMIN_xX`"
        await ctx.respond(ephemeral=True, content=error_message)
        return False

    # If we got here, the arguments are valid and safe to act upon
    if guild_permission_bank.modify_user_id_list("admin", "add", member_to_admin.id, ctx.guild.id) == False:
        await ctx.respond(ephemeral=True, content=f"{name_of_member_to_admin} is already a bot admin in this guild.")
        return False

    await ctx.respond(ephemeral=True, content=f"Promoted {name_of_member_to_admin} to bot admin in this guild.")
    return True



# Define function for letting bot owner remove bot admins
@admin_slash_command_group.command(
    name="remove",
    description="Remove a member from my list of trusted users in this guild.",
)
async def admin_remove(
    ctx,
    name_of_member_to_unadmin: discord.Option(str, description="The name of the member you want to blacklist.")
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
        error_message += f"\n`/settings unadmin name_of_member_to_unadmin: Xx_L33T.guild.ADMIN_xX`"
        await ctx.respond(ephemeral=True, content=error_message)
        return False

    # If we got here, the arguments are valid and safe to act upon
    if guild_permission_bank.modify_user_id_list("admin", "remove", member_to_unadmin.id, ctx.guild.id) == False:
        await ctx.respond(ephemeral=True, content=f"{name_of_member_to_unadmin} is already not a bot admin in this guild.")
        return False

    await ctx.respond(ephemeral=True, content=f"Removed {name_of_member_to_unadmin} as bot admin in this guild.")
    return True



# TODO: comment
@admin_slash_command_group.command(
    name="list",
    description="List the members I trust in this guild.",
    checks=[]
)
async def admin_list(ctx):
    admin_user_id_list = guild_permission_bank.get_user_id_list("admin", ctx.guild.id)
    response = ""
    for user_id in admin_user_id_list:
        response += f"<@{user_id}>,"
    if response == "":
        await ctx.respond(ephemeral=True, content=f"I have no admins in this guild.")
    else:
        await ctx.respond(ephemeral=True, content=f"[{response}]")
    return True



########
# Lock #
########



# Create slash command sub-group
lock_slash_command_group = settings_slash_command_group.create_subgroup(
    name = "lock",
    description="Commands that affect whether all non-admins can use the bot",
    #guild_ids = default,
    guild_only = True,
    #nsfw = default,
    #default_member_permissions = default,
    #checks=[application_context_checks.assert_author_is_bot_owner]
    #name_localizations = default,
    #description_localizations = default,
)


# Define function for letting admin pause bot
@lock_slash_command_group.command(
    name="start",
    description="Make me unresponsive to non-admin commands.",
    checks=[application_context_checks.assert_bot_is_accepting_non_admin_commands]
)
async def settings_pause(ctx):
    guild_permission_bank.set_is_locked(True, ctx.guild.id)
    await ctx.respond(ephemeral=False, content=f"I will no longer accept non-admin commands until the next `/settings lock stop`.")
    return True



# Define function for letting admin unpause bot
@lock_slash_command_group.command(
    name="stop",
    description="Make me responsive to non-admin messages.",
    checks=[application_context_checks.assert_bot_is_not_accepting_non_admin_commands]
)
async def settings_unpause(ctx):
    guild_permission_bank.set_is_locked(False, ctx.guild.id)
    await ctx.respond(ephemeral=False, content=f"I will accept non-admin commands until the next `/settings lock start`.")
    return True



#########
# Other #
#########



# Define function for letting admin kill bot
@settings_slash_command_group.command(
    name="kill",
    description="Kill this bot instance for all guilds."
)
async def settings_kill(ctx):
    await ctx.respond(ephemeral=False, content=f"Powering off. Goodbye!")
    await ctx.bot.close()
    return True
