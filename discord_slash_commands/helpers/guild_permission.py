# ======================= #
# Import public libraries #
# ======================= #

# General discord API
import discord

# Custom class for interfacing with JSON files
import discord_slash_commands.helpers.json_list as json_list

# Import operating system module
import os

# Import function for loading environment variables
from dotenv import load_dotenv

# =========================== #
# Define underlying structure #
# =========================== #

# Return the bot owner's Discord user ID
def get_bot_owner_discord_user_id() -> int:
    load_dotenv()
    return int(os.getenv("BOT_OWNER_DISCORD_USER_ID"))



# Define an instance of information held user permissions for a single guild
class GuildPermission(json_list.JSONListItem):
    def __init__(
        self,
        guild_id: int = 0,
        is_locked: bool = False,
        blacklist_user_id_list: list = [],
        admin_user_id_list: list = [get_bot_owner_discord_user_id()]
    ):
        # The ID of the guild these permissions will apply to
        self.guild_id = guild_id
        # When the server is 'locked', it is not accepting commands from non-admin users
        # Locking the bot is useful for temporarily blocking spam, small debugging, and doing small maintenance
        self.is_locked = is_locked
        # A dictionary holding the different types of permissions a user can have in a guild
        self.dict_of_user_id_list = {
            # A list of what user IDs are not allowed to use my commands in this guild
            # Useful for, for example, blocking someone from using TTS nefariously, while someone else still needs to legitimately use it
            "blacklisted": blacklist_user_id_list,
            # A list of what user IDs I trust to call my more sensitive commands, for example, killing the bot and blacklisting others
            "admin": admin_user_id_list
        }

    # Convert class to JSON format
    def to_dict(self) -> dict:
        return {
            "gid": self.guild_id,
            "locked": self.is_locked,
            "uid_dict": self.dict_of_user_id_list,
        }

    # Read class from JSON format
    def from_dict(self, dictionary: dict) -> None:
        self.guild_id = dictionary["gid"]
        self.is_locked = dictionary["locked"]
        self.dict_of_user_id_list = dictionary["uid_dict"]

    # Return a copy of this class (by value, not by reference)
    def copy(self):
        return GuildPermission(
            self.guild_id,
            self.is_locked,
            self.dict_of_user_id_list["blacklisted"],
            self.dict_of_user_id_list["admin"],
        )



# Define an instance of information held user permissions for all guilds
class GuildPermissionBank(json_list.JSONList):
    # Define function for changing a list from GuildPermission.dict_of_user_id_list for guild_id
    def modify_user_id_list(self, list_name: str, list_operation: str, user_id: int, guild_id: int):
        # Do not allow illegal operations or operands
        if not(list_name == "blacklisted" or list_name == "admin") or not(list_operation == "add" or list_operation == "remove"):
            return False

        # Get the latest updates
        self.sync()

        # Get or create a GuildPermission for guild_id
        match_index = self.get_list_item_index(lambda user_privelage, guild_id: user_privelage.guild_id == guild_id, guild_id)
        if match_index < 0:
            match_index = len(self.list)
            self.list.append(GuildPermission(guild_id))
        
        # Do list_operation, don't self.write() if it doesn't modify any data
        if list_operation == "add":
            if user_id in self.list[match_index].dict_of_user_id_list[list_name]:
                return False
            self.list[match_index].dict_of_user_id_list[list_name].append(user_id)
        elif list_operation == "remove":
            if user_id not in self.list[match_index].dict_of_user_id_list[list_name]:
                return False
            self.list[match_index].dict_of_user_id_list[list_name].remove(user_id)
        
        # Save the latest updates
        self.write()
        return True

    # Define function for getting a list from GuildPermission.dict_of_user_id_list for guild_id
    def get_user_id_list(self, list_name: str, guild_id: int) -> list:
        # Do not allow illegal operations
        if not(list_name == "blacklisted" or list_name == "admin"):
            return []

        # Get the latest changes
        self.sync()

        # Get or create a GuildPermission for guild_id
        match_index = self.get_list_item_index(lambda user_privelage, guild_id: user_privelage.guild_id == guild_id, guild_id)
        if match_index < 0:
            match_index = len(self.list)
            self.list.append(GuildPermission(guild_id))

        # Return match
        return self.list[match_index].dict_of_user_id_list[permission_type]

    # Define function for letting user query other user's permissions
    def user_has_permission(self, permission_type: str, user_id: int, guild_id: int) -> bool:
        # If querying whether the user is a bot owner, can do a simple check and exit early
        if permission_type == "bot owner":
            return user_id == get_bot_owner_discord_user_id()

        # Return whether the user is in the list of people with this special permission
        return user_id in self.get_user_id_list(permission_type, guild_id)

    # Define function for changing whether guild_id is locked
    def set_is_locked(self, new_lock_value: bool, guild_id: int) -> None:
        # Get the latest updates
        self.sync()

        # Get or create a GuildPermission for guild_id, if no changes will happen, don't save them
        match_index = self.get_list_item_index(lambda user_privelage, guild_id: user_privelage.guild_id == guild_id, guild_id)
        if match_index < 0:
            match_index = len(self.list)
            self.list.append(GuildPermission(guild_id))
        elif self.list[match_index].is_locked == new_lock_value:
            return

        # Set the new is_locked value
        self.list[match_index].is_locked = new_lock_value

        # Save the latest updates
        self.write()

    # Define function for querying whether guild_id is locked
    def get_is_locked(self, guild_id: int) -> bool:
        # Get the latest updates
        self.sync()

        # Get or create a GuildPermission for guild_id
        match_index = self.get_list_item_index(lambda user_privelage, guild_id: user_privelage.guild_id == guild_id, guild_id)
        if match_index < 0:
            match_index = len(self.list)
            self.list.append(GuildPermission(guild_id))

        # Return whether this guild is_locked
        return self.list[match_index].is_locked



# Create class instances
guild_permission_instance = GuildPermission()
guild_permission_bank = GuildPermissionBank(
    file_directory = "json",
    file_name = "user_permission_bank.json",
    list_type_instance = guild_permission_instance,
    #max_file_size_in_bytes = default
)
