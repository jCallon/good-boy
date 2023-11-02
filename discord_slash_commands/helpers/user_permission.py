"""Stores what users have what permissions for this bot in each guild.

This file defines classes and functions for storing what users have what
permissions for this bot in what guilds. This bot does not need or want to
create or modify guild roles. The less permissions the better.
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



# TODO: can happlity remove users with default permissions, same for tts and other tables? maybe have sperate thread to clean them or do it on an event?
class UserPermission():
    """TODO.

    TODO.

    Attributes:
        guild_id: TODO
        user_id: TODO
        is_blacklisted: TODO
        is_admin: TODO
    """
    def __init__(
        self,
        ctx: discord.ApplicationContext = None
    ):
        """TODO.

        TODO.

        Args:
            TODO
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
        else
            self.user_id = 0

        # Fill self.is_blacklisted
        # Just use default value of False
        self.is_blacklisted = False

        # Fill self.is_admin
        # Just use default value of False
        self.is_admin = False

        # Overwrite members with ones from table if defined
        self.read(self.guild_id, self.user_id)

    def save(self) -> bool:
        """Save this UserPermission instance into the database.

        Insert this UserPermission into the permissions database. Each guild
        has its own table named after its guild id. TODO

        Args:
            self: This UserPermission

        Returns:
            Whether the operation was successful. It may not be, for example,
            if the connection to the database, or the database itself, is not
            found or is faulty.
        """
        # Check safety of parameters
        if not (
            isinstance(self.guild_id, int) and \
            isinstance(self.user_id, int) and \
            isinstance(self.is_blacklisted, bool) and \
            isinstance(self.is_admin, bool)
        ):
            return False

        # Cast booleans to integers
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
        """Copy UserPermission matching TODO from database.

        Try to find the row in the table guild_$guild_id matching user_id for
        the TTS user information database. If it exists, overwrite the members
        of this UserPermission with its data entries.

        Args:
            self: This UserPermission
            guild_id: Users may have preferences that differ per guild. This
                parameter lets you specify the guild you are checking this
                user's preferences for.
            user_id: The ID of the user you want to know the preferences of.

        Returns:
            Whether the operation was successful. It may not be, for example,
            if the connection to the database, or the database itself, is not
            found or is faulty. Or, this user simply does not have preferences
            in this guild.
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

        # If there was no match, return failure and don't change this
        # UserPermission's members
        if status.success is False:
            return False

        # There was a match, overwrite this UserPermission's members with
        # values from the database
        result = status.result[0]
        self.guild_id = guild_id
        self.user_id = user_id
        self.is_blacklisted = bool(result[1])
        self.is_admin = bool(result[2])
        return True
