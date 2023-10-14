# ======================= #
# Import public libraries #
# ======================= #

# General discord API
import discord

# Custom class for interfacing with JSON files
import discord_slash_commands.helpers.json_list as json_list

# =========================== #
# Define underlying structure #
# =========================== #

# Define an instance of information on user permissions for a single guild
class UserPermission(json_list.JSONListItem):
    def __init__(
        self,
        user_id: int = 0,
        blacklist_user_id_list: list = [],
        admin_user_id_list: list = []
    ):
        # The ID of the user who is having info kept on them
        self.guild_id = guild_id
        # A dictionary holding the different types of permissions a user can have in a guild
        self.dict_of_user_id_list =
        {
            # What users this guild blacklisted from using this bot
            "blacklisted": blacklist_user_id_list,
            # What users this guild considers admins for this bot
            "admin": admin_user_id_list
        }

    # Convert class to JSON format
    def to_dict(self) -> dict:
        return {
            "gid": self.guild_id,
            "uid_dict": self.dict_of_user_id_list,
        }

    # Read class from JSON format
    def from_dict(self, dictionary: dict) -> None:
        self.guild_id = dictionary["gid"]
        self.dict_of_user_id_list = dictionary["uid_dict"]



# Define a list of information on user permissions for a all guilds
class UserPermissionBank(json_list.JSONList):
    # Define function for letting a user modify other user's permissions
    def modify_user_permission(self, list_type: str, list_operation: str, user_id: int, guild_id: int):
        # Do not allow illegal operations or operands
        if self.dict_of_user_id_list[list_type] == None or not(list_operation == "add" or list_operation == "remove"):
            return False

        # Get the latest updates
        self.sync()

        # Get or create a UserPermission for guild_id
        match_index = self.get_list_item_index(lambda user_privelage: return user_privelage.guild_id == guild_id), guild_id)
        if match_index < 0:
            match_index = len(self.list)
            self.list.append(UserPermission(guild_id, [], []))
        
        # Do list_operation, don't self.write() if it doesn't modify any data
        if list_operation == "add":
            if user_id in self.list[match_index].dict_of_user_id_list[list_type]:
                return False
            self.list[match_index].dict_of_guild_id_list[list_type].append(guild_id)
        elif list_operation == "remove":
            if user_id not in self.list[match_index].dict_of_user_id_list[list_type]:
                return False
            self.list[match_index].dict_of_guild_id_list[list_type].remove(guild_id)
        
        # Save the latest updates
        self.write()
        return True

    # TODO: comment
    def get_user_permission(self, permission_type: str, guild_id: int) -> list:
        # Do not allow illegal operations
        if not(permission_type == "admin" or permission_type =="blacklisted"):
            return []

        # Get the latest changes
        self.sync()

        # Get a UserPermission for guild_id, if there is none, there's no way this user has a special permission for this guild
        match_index = self.get_list_item_index(lambda user_privelage: return user_privelage.guild_id == guild_id), guild_id)
        if match_index < 0:
            return []

        # Return match
        return self.list[match_index].dict_of_user_id_lists[permission_type]
        

    # Define function for letting user query other user's permissions
    def user_has_permission(self, permission_type: str, user_id: int, guild_id: int) -> bool:
        # If querying whether the user is a bot owner, can do a simple check and exit early
        if permission_type == "bot owner":
            return user_id == dotenv.bot_owner_discord_user_id

        # The bot owner always has admin privelages
        if permission_type == "admin" and user_id == dotenv.bot_owner_discord_user_id:
            return True

        # Return whether the user is in the list of people with this special permission
        return user_id in self.get_user_permission(permission_type, guild_id)



# Create class instances
user_permission_instance = UserPermission()
user_permission_bank = UserPermissionBank(
    file_directory = "json",
    file_name = "user_permission_bank.json",
    list_type_instance = tts_user_preference_instance,
    #max_file_size_in_bytes = default
)
