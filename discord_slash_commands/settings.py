"""PyCord.SlashCommand for configuring user permissions for this bot.

This file defines slash commands for letting admins of this bot modify who can
do what for a given guild. These commands are largely uneeded in a guild of
trusted friends, but are very useful in growing or large guilds to keep
malicious/annoying activity enabled by the bot to a minimum.
"""

#==============================================================================#
# Import libraries                                                             #
#==============================================================================#

# Import Discord Python API
import discord

# Import user permissions for each guild
import discord_slash_commands.helpers.guild_permission as guild_permission
from discord_slash_commands.helpers.guild_permission \
import guild_permission_bank

# Import functions for asserting bot state
import discord_slash_commands.helpers.application_context_checks as ctx_check

#==============================================================================#
# Define underlying structure                                                  #
#==============================================================================#

# Create slash command group
settings_slash_command_group = discord.SlashCommandGroup(
    checks = [ctx_check.assert_author_is_admin],
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

#------------------------------------------------------------------------------#
# Blacklist                                                                    #
#------------------------------------------------------------------------------#

# Create slash command sub-group
blacklist_slash_command_group = settings_slash_command_group.create_subgroup(
    name = "blacklist",
    description="Commands affecting which non-admins can use the bot",
    #guild_ids = default,
    guild_only = True,
    #nsfw = default,
    #default_member_permissions = default,
    #checks = default,
    #name_localizations = default,
    #description_localizations = default,
)



@blacklist_slash_command_group.command(
    name="add",
    description="Ban someone (ex. annoying/abusive) from using me."
)
async def blacklist_add(
    ctx,
    member_name: discord.Option(
        str,
        description="The name of the member you want to blacklist."
    ),
    reason: discord.Option(
        str,
        description="The reason you are blacklisting this member."
    )):
    """Tell bot to blacklist a member from most of its commands in this guild.

    Tell bot to add the member matching member_name to its list of blacklisted
    members for this guild. Blacklisted members will not be able to call most
    commands from this bot. As of writing this, the only exception should be
    `/random *` and `/settings admin list`.

    Args:
        ctx: The context this SlashCommand was called under
        member_name: The name of the member of this guild to affect
        reason: The reason for blacklisting the member matching member_name
    """
    # TODO: store reason?
    # Determine if the author's arguments are valid
    err_msg = ""
    member_to_blacklist = ctx.guild.get_member_named(member_name)
    if member_to_blacklist is None:
        err_msg += f"\nI could not find {member_name} in this guild."
    if member_to_blacklist != None and \
        guild_permission_bank.user_has_permission(
            "admin",
            member_to_blacklist.id,
            ctx.guild.id
        ) is True:
        err_msg += "\nYou cannot blacklist other admins. " \
            + "Please ask the bot owner, " \
            + f"<@{guild_permission.get_bot_owner_discord_user_id()}> " \
            + "to un-admin the offending admin."
    if len(reason) < 1:
        err_msg += "\nPlease give a reason you are blacklisting this member " \
            + "(it will be visible to all unless deleted for record-keeping)."

    # If the author's arguments were invalid,
    # give them verbose error messages and an example to help them
    if err_msg != "":
        err_msg += "\nHere's an example command." \
            + "\nBan Sell Sell $ell! from using this bot." \
            + "\n`/admin blacklist add member_name: Sell Sell $ell! " \
            + "reason: Used the bot for spamming users with advertisements " \
            + "of their merchandise.`"
        await ctx.respond(ephemeral=True, content=err_msg)
        return False

    # If we got here, the arguments are valid and safe to act upon
    # Try to add this user to the list of blacklisted users for this guild
    if guild_permission_bank.modify_user_id_list(
        "blacklisted",
        "add",
        member_to_blacklist.id,
        ctx.guild.id
    ) is False:
        # TODO: can fail for file IO reasons too
        await ctx.respond(
            ephemeral=True,
            content=f"{member_name} is already blacklisted in this guild."
        )
        return False

    await ctx.respond(
        ephemeral=False,
        content=f"Blacklisted {member_name} in this guild."
    )
    return True



@blacklist_slash_command_group.command(
    name="remove",
    description="Unban someone previously banned from using me."
)
async def blacklist_remove(
    ctx,
    member_name: discord.Option(
        str,
        description="The name of the member you want to unblacklist."
    )
):
    """Tell bot to unblacklist a member from most of its commands in this guild.

    Tell bot to remove the member matching member_name to its list of
    blacklisted members for this guild.

    Args:
        ctx: The context this SlashCommand was called under
        member_name: The name of the member of this guild to affect
    """
    # Determine if the author's arguments are valid
    err_msg = ""
    member_to_unblacklist = ctx.guild.get_member_named(member_name)
    if member_to_unblacklist is None:
        err_msg += f"\nI could not find {member_name} in this guild."

    # If the author's arguments were invalid,
    # give them verbose error messages and an example to help them
    if err_msg != "":
        err_msg += "\nHere's an example command." \
            + "\nUnban Sell Sell $ell! from using this bot." \
            + "\n`/admin blacklist remove member_name: Sell Sell $ell!`"
        await ctx.respond(ephemeral=True, content=err_msg)
        return False

    # If we got here, the arguments are valid and safe to act upon
    # Try to remove this user from the list of blacklisted users for this guild
    if guild_permission_bank.modify_user_id_list(
        "blacklisted",
        "remove",
        member_to_unblacklist.id,
        ctx.guild.id
    ) is False:
        # TODO: can fail for file IO reasons too
        await ctx.respond(
            ephemeral=True,
            content=f"{member_name} is already not blacklisted in this guild."
        )
        return False

    await ctx.respond(
        ephemeral=False,
        content=f"Unblacklisted {member_name} in this guild."
    )
    return True



@blacklist_slash_command_group.command(
    name="list",
    description="See the members blacklisted in this guild."
)
async def blacklist_list(ctx):
    """Tell bot to give a list of members who are blacklisted in this guild.

    Tell the bot to respond with a message containing each member in this guild
    who is blacklisted.
    """
    blacklist_user_id_list = guild_permission_bank.get_user_id_list(
        "blacklisted",
        ctx.guild.id
    )

    if blacklist_user_id_list == []:
        await ctx.respond(
            ephemeral=True,
            content="I have no one blacklisted in this guild."
        )
        return True

    response = ""
    for user_id in blacklist_user_id_list:
        response += f"<@{user_id}>,"
    await ctx.respond(ephemeral=True, content=f"[{response}]")
    return True



#------------------------------------------------------------------------------#
# Admin                                                                        #
#------------------------------------------------------------------------------#

# Create slash command sub-group
admin_slash_command_group = settings_slash_command_group.create_subgroup(
    name = "admin",
    description="Commands to affect who has elevated privelages for this bot",
    #guild_ids = default,
    guild_only = True,
    #nsfw = default,
    #default_member_permissions = default,
    checks=[ctx_check.assert_author_is_bot_owner]
    #name_localizations = default,
    #description_localizations = default,
)



@admin_slash_command_group.command(
    name="add",
    description="Add a member to my list of trusted users in this guild.",
)
async def admin_add(
    ctx,
    member_name: discord.Option(
        str,
        description="The name of the member you want to admin."
    )
):
    """Tell bot to add a member as one of its admins in this guild.

    Tell bot to add the member matching member_name to its list of admins for
    this guild. Admins of this bot can use more sensitive commands, such as
    disconnecting the bot and moderating the the bot's blacklists. Only the bot
    owner can add or remove admins for this bot.

    Args:
        ctx: The context this SlashCommand was called under
        member_name: The name of the member of this guild to affect
    """
    # Determine if the author's arguments are valid
    err_msg = ""
    member_to_admin = ctx.guild.get_member_named(member_name)
    # TODO: remove debugging
    print(ctx.guild.members)
    if member_to_admin is None:
        err_msg += f"\nI could not find {member_name} in this guild."

    # If the author's arguments were invalid,
    # give them verbose error messages and an example to help them
    if err_msg != "":
        err_msg += "\nHere's an example command." \
            + "\nAdd Xx_L33T.guild.ADMIN_xX as on of my bot admins." \
            + "\n`/settings admin add member_name: Xx_L33T.guild.ADMIN_xX`"
        await ctx.respond(ephemeral=True, content=err_msg)
        return False

    # If we got here, the arguments are valid and safe to act upon
    # Add the member to the list of admins
    if guild_permission_bank.modify_user_id_list(
        "admin",
        "add",
        member_to_admin.id,
        ctx.guild.id
    ) is False:
        # TODO: can fail for file IO reasons too
        await ctx.respond(
            ephemeral=True,
            content=f"{member_name} is already one of my admins in this guild."
        )
        return False

    await ctx.respond(
        ephemeral=True,
        content=f"Promoted {member_name} to one of my admins in this guild."
    )
    return True



@admin_slash_command_group.command(
    name="remove",
    description="Remove a member from my list of trusted users in this guild.",
)
async def admin_remove(
    ctx,
    member_name: discord.Option(
        str,
        description="The name of the member you want to blacklist."
    )
):
    """Tell bot to remove a member as one of its admins in this guild.

    Tell bot to add the member matching member_name to its list of admins for
    this guild. Only the bot owner can add or remove admins for this bot.

    Args:
        ctx: The context this SlashCommand was called under
        member_name: The name of the member of this guild to affect
    """
    # Determine if the arguments are valid
    err_msg = ""
    member_to_unadmin = ctx.guild.get_member_named(member_name)
    if member_to_unadmin is None:
        err_msg += f"\nI could not find {member_name} in this guild."

    # If the author's arguments were invalid,
    # give them verbose error messages and an example to help them
    if err_msg != "":
        err_msg += "\nHere's an example command." \
            + "\nRemove Xx_L33T.guild.ADMIN_xX as a bot admin for me." \
            + "\n`/settings admin remove member_name: Xx_L33T.guild.ADMIN_xX`"
        await ctx.respond(ephemeral=True, content=err_msg)
        return False

    # If we got here, the arguments are valid and safe to act upon
    # Remove the member from the list of admins
    if guild_permission_bank.modify_user_id_list(
        "admin",
        "remove",
        member_to_unadmin.id,
        ctx.guild.id
    ) is False:
        # TODO: can fail for file IO reasons too
        await ctx.respond(
            ephemeral=True,
            content=f"{member_name} is already not in my admins in this guild."
        )
        return False

    await ctx.respond(
        ephemeral=True,
        content=f"Removed {member_name} as one of my admins in this guild."
    )
    return True



@admin_slash_command_group.command(
    name="list",
    description="List the members I trust in this guild.",
    checks=[]
)
async def admin_list(ctx):
    """Tell bot to give a list of members who are currently its admins.

    Tell the bot to respond with a message containing each member in this guild
    who is an admin fo the bot.
    """
    admin_user_id_list = guild_permission_bank.get_user_id_list(
        "admin",
        ctx.guild.id
    )

    if admin_user_id_list == []:
        await ctx.respond(
            ephemeral=True,
            content="I have no admins in this guild."
        )
        return True

    response = ""
    for user_id in admin_user_id_list:
        response += f"<@{user_id}>, "
    await ctx.respond(ephemeral=True, content=f"[{response}]")
    return True



#------------------------------------------------------------------------------#
# Lock                                                                         #
#------------------------------------------------------------------------------#

# Create slash command sub-group
lock_slash_command_group = settings_slash_command_group.create_subgroup(
    name = "lock",
    description="Commands that affect whether all non-admins can use the bot",
    #guild_ids = default,
    guild_only = True,
    #nsfw = default,
    #default_member_permissions = default,
    #checks=[ctx_check.assert_author_is_bot_owner]
    #name_localizations = default,
    #description_localizations = default,
)


@lock_slash_command_group.command(
    name="start",
    description="Make me deny commands from non-admins.",
    checks=[ctx_check.assert_bot_is_accepting_non_admin_commands]
)
async def settings_pause(ctx):
    """Tell bot to not accept commands from non-admin members in this guild.

    Tell the bot to stop letting members who are not admins of this bot call
    most of its commands.

    Args:
        ctx: The context this SlashCommand was called under
    """
    # TODO: this function should be able to fail for file IO reasons
    guild_permission_bank.set_is_locked(True, ctx.guild.id)
    await ctx.respond(
        ephemeral=False,
        content="I'll stop accepting commands from non-admins until the next " \
        + "`/settings lock stop`."
    )
    return True



@lock_slash_command_group.command(
    name="stop",
    description="Make me stop denying commands from non-admins.",
    checks=[ctx_check.assert_bot_is_not_accepting_non_admin_commands]
)
async def settings_unpause(ctx):
    """Tell bot to accept commands from non-admin members in this guild.

    Tell the bot to start letting members who are not admins of this bot call
    most of its commands.

    Args:
        ctx: The context this SlashCommand was called under
    """
    # TODO: this function should be able to fail for file IO reasons
    guild_permission_bank.set_is_locked(False, ctx.guild.id)
    await ctx.respond(
        ephemeral=False,
        content="I'll start accepting commands from non-admins until the " \
            + "next `/settings lock start`."
    )
    return True



#------------------------------------------------------------------------------#
# Other                                                                        #
#------------------------------------------------------------------------------#

@settings_slash_command_group.command(
    name="kill",
    description="Kill this bot instance for all guilds."
)
async def settings_kill(ctx):
    """Tell bot to stop executing.

    Close this bot's connection with Discord. `/settings pause start` should
    be used instead whenever possible, but this command exists in case that is
    ever not enough.

    Args:
        ctx: The context this SlashCommand was called under
    """
    await ctx.respond(ephemeral=False, content="Powering off. Goodbye!")
    await ctx.bot.close()
    return True
