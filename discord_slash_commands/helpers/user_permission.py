"""Stores what users have what permissions for this bot in each guild.

This file defines classes and functions for storing what users have what
permissions for this bot in what guilds. This bot does not need or want to
create or modify guild roles. The less permissions the bot requires to run
the better.
"""

#==============================================================================#
# Import libraries                                                             #
#==============================================================================#

# Import operating system module
import os

# Import function for loading environment variables
from dotenv import load_dotenv

# Import Discord Python API
import discord

# Import helper for interacting with internal database
from discord_slash_commands.helpers import sqlite

#==============================================================================#
# Define underlying structure                                                  #
#==============================================================================#

def get_bot_owner_discord_user_id() -> int:
    """Get the Discord user ID of the bot owner.

    Get the Discord user ID of the owner of this bot from the environment
    variable BOT_OWNER_DISCORD_USER_ID set in .env.

    Returns:
        The bot owner's Discord user ID as an integer.
    """
    load_dotenv()
    return int(os.getenv("BOT_OWNER_DISCORD_USER_ID"))



# Define a string you can paste if there was an error with sqlite.run
sql_error_paste_str = "Could not complete action for unknown reasons." \
+ f"\nPlease ask the bot owner, <@{get_bot_owner_discord_user_id()}>, " \
+ "to look into the issue and give them details on what happened." \



# TODO: can happily remove users with default permissions, same for tts and
# other tables? maybe have seperate thread to clean them periodically or do
# it on an event?
class UserPermission():
    """Define an instance of info held on a user for permissions.

    Define an instance of information held on a user for keeping track of how
    they are allowed to use the bot. Information is held per-guild, where each
    guild has its own table, guild_$guild_id.

    Attributes:
        guild_id: The unique identifier of the guild where the user's
            permissions are being specified.
        user_id: The unique identifier of the user whose permissions are being
            specified.
        is_blacklisted: Whether to consider this user as 'blacklisted', meaning
            they are not allowed to use most of this bot's commands.
        is_admin: Whether to consider this user an 'admin', meaning they are a
            highly-trusted user allowed to execute more dangerous commands such
            as killing the bot or blacklisting others from using the bot.
    """
    def __init__(self, ctx: discord.ApplicationContext = None):
        """Initialize this UserPermission.

        Set the members of this UserPermission based on members from ctx.

        Args:
            self: This UserPermission
            ctx: The context a /permissions command was called from
        """
        # Fill self.guild_id
        # Sometimes a command will be sent from DMs, so it will not have a guild
        if isinstance(ctx, discord.ApplicationContext):
            self.guild_id = ctx.guild.id if ctx.guild is not None else None
        else:
            self.guild_id = 0

        # Fill self.user_id
        if isinstance(ctx, discord.ApplicationContext):
            self.user_id = ctx.author.id
        else:
            self.user_id = 0

        # Fill self.is_blacklisted
        # Just use default value of False
        self.is_blacklisted = False

        # Fill self.is_admin
        # Just use default value of False
        self.is_admin = False

        # Overwrite members with ones from table if defined and not just making
        # an empty instance of the class
        if ctx != None:
            self.read(self.guild_id, self.user_id)

    def save(self) -> bool:
        """Save this UserPermission instance into the database.

        Insert this UserPermission into the permissions database. Each guild
        has its own table named after its guild id. If a UserPermission with the
        same user_id already exists, just update its is_blacklisted and is_admin
        to match this UserPermission. 

        Args:
            self: This UserPermission

        Returns:
            Whether the operation was successful. It may not be, for example,
            if the connection to the database, or the database itself, is not
            found or is faulty.
        """
        # Check safety of parameters to prevent SQL injection
        if not (
            isinstance(self.guild_id, int) and \
            isinstance(self.user_id, int) and \
            isinstance(self.is_blacklisted, bool) and \
            isinstance(self.is_admin, bool)
        ):
            return False

        # Cast booleans to integers, bool is not a SQLite datatype, but int is
        is_blacklisted = int(self.is_blacklisted)
        is_admin = int(self.is_admin)

        # Execute SQL query
        return sqlite.run(
            file_name = "permissions",
            query = f"INSERT INTO guild_{self.guild_id} VALUES "\
                + f"({self.user_id},{is_blacklisted},{is_admin}) " \
                + "ON CONFLICT(user_id) DO UPDATE SET " \
                + f"is_blacklisted={is_blacklisted},is_admin={is_admin}",
            query_parameters = (),
            commit = True
        ).success is True

    def read(self, guild_id: int, user_id: int) -> bool:
        """Copy UserPermission matching user_id from database.

        Try to find the row in the table guild_$guild_id matching user_id for
        the Permissions user database. If it exists, overwrite the members
        of this UserPermission with its data entries.

        Args:
            self: This UserPermission
            guild_id: Users may have permissions that differ per guild. This
                parameter lets you specify the guild you are getting this
                user's preferences for.
            user_id: The ID of the user you want to know the preferences of.

        Returns:
            Whether the operation was successful. It may not be, for example,
            if the connection to the database, or the database itself, is not
            found or is faulty.
        """
        # Check safety of parameters
        if not (isinstance(guild_id, int) and isinstance(user_id, int)):
            return False

        # Execute SQL query
        status = sqlite.run(
            file_name = "permissions",
            query = "SELECT is_blacklisted,is_admin FROM " \
                + f"guild_{guild_id} WHERE user_id={user_id}",
            query_parameters = (),
            commit = False
        )

        # If there was an error executing the query, return failure
        if status.success is False:
            return False

        # If the query was sucessful but simply had no results, return success
        # and set this UserPermission to default permissions
        self.guild_id = guild_id
        self.user_id = user_id
        if status.result == []:
            self.is_blacklisted = False
            self.is_admin = False
            return True

        # There was a match, overwrite this UserPermission's members with
        # values from the database
        result = status.result[0]
        self.is_blacklisted = bool(result[0])
        self.is_admin = bool(result[1])
        return True
