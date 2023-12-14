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

# Import functions for asserting bot state
import discord_slash_commands.helpers.application_context_checks as ctx_check

# Import helper for interacting with internal database
from discord_slash_commands.helpers import sqlite

# Import user permissions for each guild
import discord_slash_commands.helpers.user_permission as user_perm

#==============================================================================#
# Define underlying structure                                                  #
#==============================================================================#

# Create slash command group
permissions_slash_command_group = discord.SlashCommandGroup(
    #checks = default,
    #default_member_permissions = default,
    description = "Commands that affect who has what permissions over me",
    #description_localizations = default,
    #guild_ids = default,
    guild_only = True,
    name = "permissions",
    #name_localizations = default,
    #nsfw = default,
    #parent = default
)



@permissions_slash_command_group.command(
    name="modify",
    description="Modify what permissions someone has over me in this guild.",
    checks = [ctx_check.assert_author_is_admin]
)
async def permission_modify(
    ctx,
    member_name: discord.Option(
        str,
        description="The name of the member you want to affect."
    ),
    permission: discord.Option(
        str,
        description="The permission you wish to modify for member_name.",
        choices=["blacklist", "admin"]
    ),
    operation: discord.Option(
        str,
        description="How you wish to modify the permission for member_name.",
        choices=["add", "remove"]
    ),
):
    """Tell bot, for member_name, do operation for permission.

    Tell the bot what user's permissions to modify in this guild and what to
    modify it to.

    Args:
        ctx: The context this SlashCommand was called under
        member_name: The name of the member to affect
        permission: The permission of the member to affect
        operation: How to modify the permission to affect
    """
    # Update and read member cache, if you don't do this get_member_named may
    # not work for members who have not recently interacted with the bot
    await ctx.guild.query_members(member_name)
    member = ctx.guild.get_member_named(member_name)

    # Determine if the author's arguments are valid
    # If the author's arguments were invalid,
    # give them verbose error messages and an example to help them
    if member is None:
        await ctx.respond(
            ephemeral=True,
            content=f"I could not find {member_name} in this guild." \
            + "\nHave you tried using their discriminator instead of their " \
            + "display name or nick?" \
            + "\nHere's an example command." \
            + "\nMake Jasper an admin for this bot in this guild." \
            + "\n`/permissions modify member_name: Jasper permission: " \
            + "admin operation: add`"
        )
        return False

    # If we got here, the arguments are valid and safe to act upon
    # Try to add this user to the list of blacklisted users for this guild
    user_permission = user_perm.UserPermission()
    user_permission.guild_id = ctx.guild.id
    user_permission.user_id = member.id
    user_permission.read(ctx.guild.id, member.id)

    permission_value = operation == "add"
    if permission == "blacklist":
        user_permission.is_blacklisted = permission_value
    elif permission == "admin":
        user_permission.is_admin = permission_value

    if user_permission.save() is False:
        await ctx.respond(ephemeral=True, content=user_perm.sql_error_paste_str)
        return False

    await ctx.respond(
        ephemeral=False,
        content=f"Successfully did {operation} for {member_name} on "
            + f"{permission} list."
    )
    return True



@permissions_slash_command_group.command(
    name="view",
    description="See who has what permissions has over me in this guild."
)
async def permission_view(
    ctx,
    permission: discord.Option(
        str,
        description="The permission you wish to view the users of.",
        choices=["blacklist", "admin"]
    )
):
    """Tell the bot show who has what permissions over it in this guild.

    Tell the bot to give you a list of what users have permission in this guild.

    Args:
        ctx: The context this SlashCommand was called under
        permission: What permission a user should have to be included in the
            list that will be printed.
    """
    # Generate condition based on permission
    condition = ""
    if permission == "admin":
        condition = "is_admin>0"
    elif permission == "blacklist":
        condition = "is_blacklisted>0"

    # Execute SQL query
    status = sqlite.run(
        file_name = "permissions",
        query = f"SELECT user_id FROM guild_{ctx.guild.id} WHERE {condition}",
        query_parameters = (),
        commit = False
    )

    # Tell the author if the query failed
    if status.success is False:
        await ctx.respond(ephemeral=True, content=user_perm.sql_error_paste_str)
        return False

    # Tell the author if the query was successful but the results were empty
    if status.result == []:
        await ctx.respond(
            ephemeral=True,
            content="I couldn't find any members with that permission in " \
                + "this guild."
        )
        return True

    # Tell the author every member from the results
    mention_list = []
    for match_tuple in status.result:
        mention_list.append(f"<@{match_tuple[0]}>")
    await ctx.respond(ephemeral=True, content=",".join(mention_list))
    return True
