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
import discord_slash_commands.helpers.user_permission as user_perm

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
permission_slash_command_group = settings_slash_command_group.create_subgroup(
    name = "permission",
    description="TODO",
    #guild_ids = default,
    guild_only = True,
    #nsfw = default,
    #default_member_permissions = default,
    #checks = default,
    #name_localizations = default,
    #description_localizations = default,
)



@permission_slash_command_group.command(
    name="modify",
    description="TODO.",
)
async def permission_modify(
    ctx,
    member_name: discord.Option(
        str,
        description="The name of the member you want to affect."
    ),
    permission: discord.Option(
        str,
        description="The permission you wish to modify for member_name."
        options=["blacklist", "admin"]
    ),
    operation: discord.Option(
        str,
        description="What you wish to set the permission for member_name to."
        options=["add", "remove"]
    ),
):
    """TODO.

    TODO.

    Args:
        TODO
    """
    # Only the bot owner is allowed to admin or unadmin people
    if permission == "admin":
        await ctx.respond(
            ephemeral=True,
            content=f"Only the bot owner, TODO," \
                + "can change who is an isn't an admin for me."
        )
        return False

    # Update and read member cache, if you don't do this get_member_named may
    # not work for members who have no recently interacted with the bot
    await ctx.guild.query_members(member_name)
    member = ctx.guild.get_member_named(member_name)

    # Determine if the author's arguments are valid
    # If the author's arguments were invalid,
    # give them verbose error messages and an example to help them
    if member is None:
        err_msg = f"I could not find {member_name} in this guild." \
            + f"\n{example_str}"
        return False

    # If we got here, the arguments are valid and safe to act upon
    # Try to add this user to the list of blacklisted users for this guild
    user_permission = user_perm.UserPermission()
    user_permission.read(ctx.guild.id, ctx.author.id)

    new_permission_value = 0 if operation == "remove" else 1
    if permission == "blacklist":
        user_permission.is_blacklisted = new_permission_value
    elif permission == "admin":
        user_permission.is_admin = new_permission_value

    if user_permission.save() is False:
        await ctx.respond(ephemeral=True, content=sqlite.error_paste_str)

    await ctx.respond(
        ephemeral=False,
        content=f"Successfully modified {permission} list."
    )
    return True



@permission_slash_command_group.command(
    name="view",
    description="See the members with a certain permisson in this guild."
)
async def permission_view(
    ctx,
    permission: discord.Option(
        str,
        description="The permission you wish to view the users of."
        options=["blacklist", "admin"]
    )
):
    """TODO.

    TODO.

    Args:
        TODO
    """
    # Generate condition based on permission
    condition = ""
    if permission == "admin":
        condition = f"is_admin>0"
    elif permission == "blacklist":
        condition = f"is_blacklisted>0"

    # Execute SQL query
    status = sqlite.run(
        file_name = "permissions",
        query = f"SELECT user_id FROM guild_{ctx.guild.id} WHERE {condition}"
        query_parameters = (),
        commit = False
    )

    # Tell the author if the query failed
    if status.success is False:
        await ctx.respond(ephemeral=True, content=sqlite.error_paste_str)
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
    for user_id in status.result:
        mention_list.append(f"<@{user_id}>")
    await ctx.respond(ephemeral=True, content=",".join(mention_list))
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


# TODO: implement this
#@lock_slash_command_group.command(
#    name="start",
#    description="Make me deny commands from non-admins.",
#    checks=[ctx_check.assert_bot_is_accepting_non_admin_commands]
#)
#async def settings_pause(ctx):
#    """Tell bot to not accept commands from non-admin members in this guild.
#
#    Tell the bot to stop letting members who are not admins of this bot call
#    most of its commands.
#
#    Args:
#        ctx: The context this SlashCommand was called under
#    """
#    await ctx.respond(ephemeral=False, content="")
#    return True



# TODO: implement this
#@lock_slash_command_group.command(
#    name="stop",
#    description="Make me stop denying commands from non-admins.",
#    checks=[ctx_check.assert_bot_is_not_accepting_non_admin_commands]
#)
#async def settings_unpause(ctx):
#    """Tell bot to accept commands from non-admin members in this guild.
#
#    Tell the bot to start letting members who are not admins of this bot call
#    most of its commands.
#
#    Args:
#        ctx: The context this SlashCommand was called under
#    """
#    await ctx.respond(ephemeral=False, content="")
#    return True



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



@settings_slash_command_group.command(
    name="get_invite_link",
    description="Get an invite link to invite the bot to a guild.",
    checks=[ctx_check.assert_author_is_bot_owner]
)
async def settings_get_invite_link(ctx):
    """Tell bot to give you a link to invite it to other guilds.

    Generate an invite link for the bot you can use yourself or share with
    others from the permissions below.

    Args:
        ctx: The context this SlashCommand was called under
    """
    # See https://docs.pycord.dev/en/stable/api/data_classes.html#permissions
    # See the OAuth2 panel in your Discord Developer Portal too
    perm = discord.Permissions()
    # This bot does not need to create invites
    perm.create_instant_invite = False
    # This bot, although it can prevent certain members from using itself,
    # will not kick members from the guild outright
    perm.kick_members = False
    # This bot, although it can prevent certain members from using itself,
    # will not ban members from the guild outright
    perm.ban_members = False
    # This bot does not need administrator privelages in any guild
    perm.administrator = False
    # The bot does not create, delete, or create channels
    perm.manage_channels = False
    # The bot does not manage or modify guild properties
    perm.manage_guild = False
    # This bot will want to be able to add reactions to its own /poll messages
    # TODO: this command is not implemented yet, change later if needed
    perm.add_reactions = False
    # This bot does not need to access the guild audit logs
    perm.view_audit_log = False
    # This bot is not more important than any other member speaking
    perm.priority_speaker = False
    # This bot cannot video stream, only play audio
    # TODO: change this if this is ever not the case
    perm.stream = False
    # This bot does not need to view any specific channels
    # TODO: ... Right? Test it does not need this to run slash commands
    #       in-channel or see reactions to its own messages
    perm.view_channel = False
    # This is an alias for view_channel
    perm.read_messages = False
    # This bot sends messages for /reminder and /poll
    # TODO: these commands are not implemented yet, change later if needed
    perm.send_messages = False
    # This bot uses TTS in voice chat, not text chat
    perm.send_tts_messages = False
    # This bot deletes some of its own messages for cleanup purposes
    perm.manage_messages = True
    # This bot may send links to other pages
    perm.embed_links = True
    # This bot can send files via /local get
    # TODO: this command is not implemented yet, change later if needed
    perm.attach_files = False
    # This bot has no need to read messages that are not immediately to itself
    perm.read_message_history = False
    # This bot has no need to mention everyone
    perm.mention_everyone = False
    # This bot has no need for emojis from other guilds
    perm.external_emojis = False
    # This is an alias for external_emojis
    perm.use_external_emojis = False
    # This bot has no need to get guild insights
    perm.view_guild_insights = False
    # This bot connects to voice chat for a variety of reasons
    perm.connect = True
    # This bot speaks in voice chat for a variety of reasons
    perm.speak = True
    # This bot does not mute members
    perm.mute_members = False
    # This bot does not deafen members
    perm.deafen_members = False
    # This bot does not move members
    perm.move_members = False
    # This bot does not currently listen to anyone in voice chat
    # TODO: change this if this is ever not the case
    perm.use_voice_activation = False
    # This bot has no need to change its own nickname
    perm.change_nickname = False
    # This bot has no need to change other's nicknames
    perm.manage_nicknames = False
    # This bot has no need to create or edit guild-wide roles,
    # it manages its own roles internally
    perm.manage_roles = False
    # This is an alias for manage_roles
    perm.manage_permissions = False
    # This bot has no need to create, edit, or delete webhooks
    # TODO: update if this ever changes, such as for monitoring voice activity
    perm.manage_webhooks = False
    # This bot has no need to create, edit, or delete emojis,
    # it only needs to react with and read them for /poll
    perm.manage_emojis = False
    # This is an alias for manage_emojis
    perm.manage_emojis_and_stickers = False
    # This bot has no need to use slash commands, only receive them
    perm.use_slash_commands = False
    # This is an alias for use_slash_commands
    perm.use_application_commands = False
    # This bot has no way to request to speak in a stage channel
    # TODO: change if this feature is ever needed
    perm.request_to_speak = False
    # This bot has no need to manage guild events
    perm.manage_events = False
    # This bot has no need to manage threads
    perm.manage_threads = False
    # This bot has no need to create public threads
    perm.create_public_threads = False
    # This bot has no need to create private threads
    perm.create_private_threads = False
    # This bot has no need to use stickers from other guilds
    perm.external_stickers = False
    # This is an alias for external_stickers
    perm.use_external_stickers = False
    # This bot should respond in-thread if it is used in-thread
    perm.send_messages_in_threads = True
    # This bot has no need to lauch activities of any kind
    perm.start_embedded_activities = False
    # This bot has no need to moderate members, just read them for /settings
    perm.moderate_members = False

    url = discord.utils.oauth_url(
        client_id=ctx.bot.application_id,
        permissions=perm
    )
    await ctx.respond(
        ephemeral=True,
        content=url \
            + "\nPlease also enable Server Members Intent and Message " \
            + "Content Intent in Privelaged Gateway Intents under Bot in " \
            + "your Discord Developer Portal.")
    return True
