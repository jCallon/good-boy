# ======================= #
# Import public libraries #
# ======================= #

# General discord API
import discord

# =========================== #
# Define underlying structure #
# =========================== #

# Create slash command group
admin_slash_command_group = discord.SlashCommandGroup(
    checks=is_admin(guild_id),
    name="admin",
    #cooldown=, These seem like a great way to prevent file IO errors
    description="Commands that require admin permission to call them",
    guild_only=True,
)



# Make a class for storing the permissions of a user
class UserPermission(JSONListItem):
    def __init__(self, user_id: int = 0, blacklist_guild_id_list: list = [], admin_guild_id_list: list = []):
        # The ID of the user who is having info kept on them
        self.user_id = user_id
        self.dict_of_guild_id_list =
        {
            # What guilds this user is blacklisted from using this bot in
            "blacklist": blacklist_guild_id_list,
            # What guilds this user is trusted as an admin of this bot in
            "admin": admin_guild_id_list
        }

    # Convert class to JSON format
    def to_dict(self, optimize_for_space: bool = False) -> dict:
        return {
            "a" if optimize_for_space == True else "user_id": self.user_id,
            "b" if optimize_for_space == True else "dict_of_guild_id_list": self.dict_of_guild_id_list,
        }

    # Read class from JSON format
    def from_dict(self, dictionary: dict, optimize_for_space: bool = False) -> None:
        self.user_id = dictionary["a" if optimize_for_space == True else "user_id"]
        self.dict_of_dict_of_guild_id_list = dictionary["b" if optimize_for_space == True else "dict_of_guild_id_list"]



# Make a class for keeping track of who can do what
class UserPermissionBank(JSONList):
    # Define function for letting user modify other user's permissions
    def modify_user_permission(self, list_type: str, list_operation: str, user_id: int, guild_id: int):
        # Do not allow illegal operations or operands
        if self.dict_of_guild_id_list[list_type] == None or not (list_operation == "add" or list_operation == "remove"):
            return False

        # Get the latest updates
        self.sync()

        # Get or create a UserPermission for user_id
        match_index = self.get_list_item_index((user_privelage, user_id) => return user_privelage.user_id == user_id), user_id)
        if match_index < 0:
            match_index = len(self.list)
            self.list.append(UserPermission(user_id, [], []))

        # Do operation, don't self.write() if it doesn't modify any data
        if list_operation == "add":
            # Append guild_id to guild_id_list if it's not already in it
            if guild_id in self.list[match_index].dict_of_guild_id_list[list_type]:
                return False
            self.list[match_index].dict_of_guild_id_list[list_type].append(guild_id)
        elif list_operation == "remove":
            # Remove guild_id from guild_id_list if it's not already remove from it
            if guild_id not in self.list[match_index].dict_of_guild_id_list[list_type]:
                return False
            self.list[match_index].dict_of_guild_id_list[list_type].remove(guild_id)
        
        # Save the latest updates
        self.write()
        return True
        

    # Define function for letting user query other user's permissions
    def user_has_permission(self, list_type: str, user_id: int, guild_id: int) -> bool:
        # Do not allow illegal types
        if self.dict_of_guild_id_list[list_type] == None:
            return False

        # Bot owner always has admin permissions over the bot
        if self.user_is_bot_owner(user_id):
            return True

        # Get the latest changes
        self.sync()

        # Determine whether user is blacklisted from this guild
        match_index = self.get_list_item_index((user_privelage, user_id) => return user_privelage.user_id == user_id), user_id)
        if match_index < 0:
            return False
        return guild_id in self.list[match_index].dict_of_guild_id_list[list_type]

    def user_is_bot_owner(self, user_id: int):
        return user_id == dotenv.bot_owner_discord_user_id



# Create instance of UserPermissionBank
user_permission_instance = UserPermissionInstance()
user_permission_bank = UserPermissionBank("user_information", "user_permission_bank.json", user_permission_instance)



# Define function for letting admin blacklist users from using bot
@admin_slash_command_group.command(name="blacklist", description="Ban someone (ex. annoying/abusive) from using me.")
async def admin_blacklist(
    ctx,
    member_name: discord.Option(int, description="The name of the member you want to blacklist."),
    reason: discord.Option(str, description="The reason you are blacklisting this member.")
):
    # Determine if the arguments are valid
    if not user_has_permission("admin", ctx.author.id, ctx.guild.id):
        await ctx.respond("Only bot admins have permission to use this command.")
        return False
    error_message = ""
    member_to_blacklist = ctx.guild.get_member_named(member_name)
    if member_to_blacklist == None:
        error_message += f"\nI could not find a member in this guild named {member_name}."
    if user_has_permission("admin", member_to_blacklist.id, ctx.guild.id):
        error_message += f"\nYou cannot blacklist other admins. Please ask the bot owner to un-admin this user."
    if len(reason) < 1:
        error_message += f"\nPlease give a reason you are blacklisting this member for record-keeping."

    # If the user's arguments weren't valid, give them verbose error messages and an example to help them
    if error_message != "":
        error_message += f"\nHere's an example command."
        error_message += f"\nBan Sell Sell $ell! from using this bot because they use it make unsolicited advertisements."
        error_message += f"\n`\\admin blacklist \"Sell Sell $ell!\" \"Used the bot for spamming users with advertisements of their merchandise.\"`"
        await ctx.respond(error_message)
        return False

    # If we got here, the arguments are valid and safe to act upon
    # TODO
    await ctx.respond(f".")
    return True



# Define function for letting admin unblacklist users from using bot
@admin_slash_command_group.command(name="unblacklist", description="Unban someone previously banned from using me.")
async def admin_unblacklist(
    ctx,
    member_name: discord.Option(int, description="The name of the member you want to blacklist.")
):
    # Determine if the arguments are valid
    if not user_has_permission("admin", ctx.author.id, ctx.guild.id):
        await ctx.respond("Only bot admins have permission to use this command.")
        return False
    error_message = ""
    member_to_blacklist = ctx.guild.get_member_named(member_name)
    if member_to_blacklist == None:
        error_message += f"\nI could not find a member in this guild named {member_name}."

    # If the user's arguments weren't valid, give them verbose error messages and an example to help them
    if error_message != "":
        error_message += f"\nHere's an example command."
        error_message += f"\nUnban Sell Sell $ell! from using this bot. They have made ammends."
        error_message += f"\n`\\admin unblacklist \"Sell Sell $ell!\"`"
        await ctx.respond(error_message)
        return False

    # If we got here, the arguments are valid and safe to act upon
    # TODO
    await ctx.respond(f".")
    return True



# Define function for letting admin pause bot
@admin_slash_command_group.command(name="pause", description="Make me unresponsinve to non-admin messages.")
async def admin_pause(ctx):
    # Determine if the arguments are valid
    if not user_has_permission("admin", ctx.author.id, ctx.guild.id):
        await ctx.respond("Only bot admins have permission to use this command.")
        return False
    error_message = ""
    if :
        error_message += f"\n."

    # If the user's arguments weren't valid, give them verbose error messages and an example to help them
    if error_message != "":
        error_message += f"\nHere's an example command."
        error_message += f"\n."
        error_message += f"\n`\\admin `"
        await ctx.respond(error_message)
        return False

    # If we got here, the arguments are valid and safe to act upon
    await ctx.respond(f".")
    return True

# Define function for letting admin unpause bot
@admin_slash_command_group.command(name="unpause", description="Make me responsive to non-admin messages.")
async def admin_unpause(ctx):
    # Determine if the arguments are valid
    if not user_has_permission("admin", ctx.author.id, ctx.guild.id):
        await ctx.respond("Only bot admins have permission to use this command.")
        return False
    error_message = ""
    if :
        error_message += f"\n."

    # If the user's arguments weren't valid, give them verbose error messages and an example to help them
    if error_message != "":
        error_message += f"\nHere's an example command."
        error_message += f"\n."
        error_message += f"\n`\\admin `"
        await ctx.respond(error_message)
        return False

    # If we got here, the arguments are valid and safe to act upon
    await ctx.respond(f".")
    return True

# Define function for letting admin kill bot
@admin_slash_command_group.command(name="kill", description="Disconnect me from the server until I am restarted.")
async def admin_kill(ctx):
    # Determine if the arguments are valid
    if not user_has_permission("admin", ctx.author.id, ctx.guild.id):
        await ctx.respond("Only bot admins have permission to use this command.")
        return False
    error_message = ""
    if :
        error_message += f"\n."

    # If the user's arguments weren't valid, give them verbose error messages and an example to help them
    if error_message != "":
        error_message += f"\nHere's an example command."
        error_message += f"\n."
        error_message += f"\n`\\admin `"
        await ctx.respond(error_message)
        return False

    # If we got here, the arguments are valid and safe to act upon
    await ctx.respond(f".")
    return True

# Define function for letting bot owner add bot admins
@admin_slash_command_group.command(name="add", description="Trust a member as one of my admins on this server.")
async def admin_add(
    ctx,
    member_name: discord.Option(int, description="The name of the member you want to blacklist.")
):
    # Determine if the arguments are valid
    if not user_is_bot_owner(ctx.author.id):
        error_message += f"\nOnly the bot owner has permission to use this command."
        return False
    error_message = ""
    member_to_blacklist = ctx.guild.get_member_named(member_name)
    if member_to_blacklist == None:
        error_message += f"\nI could not find a member in this guild named {member_name}."

    # If the user's arguments weren't valid, give them verbose error messages and an example to help them
    if error_message != "":
        error_message += f"\nHere's an example command."
        error_message += f"\nAdd Xx_Server_Admin_xX as a bot admin for me."
        error_message += f"\n`\\admin add \"Xx_Server_Admin_xX\"`"
        await ctx.respond(error_message)
        return False

    # If we got here, the arguments are valid and safe to act upon
    await ctx.respond(f".")
    return True

# Define function for letting bot owner remove bot admins
@admin_slash_command_group.command(name="remove", description="Remove trust of a memeber as one of my admins on this server.")
async def admin_remove(
    ctx,
    member_name: discord.Option(int, description="The name of the member you want to blacklist.")
):
    # Determine if the arguments are valid
    if not user_is_bot_owner(ctx.author.id):
        error_message += f"\nOnly the bot owner has permission to use this command."
        return False
    error_message = ""
    member_to_blacklist = ctx.guild.get_member_named(member_name)
    if member_to_blacklist == None:
        error_message += f"\nI could not find a member in this guild named {member_name}."

    # If the user's arguments weren't valid, give them verbose error messages and an example to help them
    if error_message != "":
        error_message += f"\nHere's an example command."
        error_message += f"\nRemove Xx_Server_Admin_xX as a bot admin for me."
        error_message += f"\n`\\admin remove \"Xx_Server_Admin_xX\"`"
        await ctx.respond(error_message)
        return False

    # If we got here, the arguments are valid and safe to act upon
    await ctx.respond(f".")
    return True
