"""PyCord.SlashCommand for setting reminders.

This file defines slash commands for letting someone create, modify, or delete a
reminder, that may trigger once or multiple times later in guild or DM channel.
"""

#==============================================================================#
# Import libraries                                                             #
#==============================================================================#

# Import API for keeping track of time
import time

# Import API for keeping track of changes in time
import datetime
from dateutil.relativedelta import relativedelta

# Import Discord Python API
import discord

# Import Discord extended APIs to create timed tasks and organized lists
from discord.ext import pages, commands, tasks

# Import functions for asserting bot state
import discord_slash_commands.helpers.application_context_checks as ctx_check

# Import user permissions for each guild
import discord_slash_commands.helpers.user_permission as user_perm

# Import helper for interacting with internal database
from discord_slash_commands.helpers import sqlite

#==============================================================================#
# Define underlying structure                                                  #
#==============================================================================#

# Define some constants to avoid copy/paste
DB_FILE_NAME = "reminders"
DB_TABLE_NAME = "outstanding_reminders"
TIME_FORMAT = "%Y%b%d %H:%M"
TIME_FORMAT_EXAMPLE = "YYYYMMMDD HH:MM"
BOT_OWNER_TIMEZONE = "PST"



def get_guild_for_channel_id(
    bot: discord.Bot,
    channel_id: int
):
    """Using bot, get the discord.Guild for a given channel id.

    Use bot.get_channel(channel_id) to try to get the channel coressponding to
    channel_id. Not all channels belong to guilds, so depending on the type of
    channel returned, there will be no coressponding guild for a channel_id.

    Args:
        bot: A bot instance to call bot.get_channel on
        channel_id: The channel id to search for the guild of

    Returns:
        The discord.Guild for channel_id, if none exists, None.
    """
    channel = bot.get_channel(channel_id)
    if isinstance(channel, (discord.abc.GuildChannel, discord.abc.Thread)):
        return channel.guild
    return None



class Reminder():
    """Define an instance of info held on a reminder for later recall.

    Define an instance of information held on a reminder so it may be remembered
    and correctly recalled at the right time, for the right amount of times in
    the future.

    Attributes:
        reminder_id: A unique identifier for this reminder, because no other
            field is guaranteed to be unique between reminders. For example: 5.
            Once a reminder has expired, it will be cleared from the database,
            and its reminder_id may be reused.
        author_user_id: The Discord user ID of the author of this reminder. For
            knowing who @mention with the reminder. For example: 7702529056.
        channel_id: The ID of the Discord channel where this reminder was
            issued. For knowing where to put the message containing the
            reminder once it's due. For example: 49012672219.
        recurrence_type: Whether this this reminder should trigger again
            (N)ever, (D)aily, (W)eekly, (M)onthly, or (Y)early. For example:
            "N".
        next_occurrence_time: The time this reminder should next be sent
            out. Measured in seconds since the last epoch. For example: 1000.
        expiration_time: The time after which this reminder should expire and
            never occur again. Measured in seconds since the last epoch. For
            example: 20000. Used to know when it is safe to delete the reminder
            from the database and stop sending messages for it.
        content: The content of the reminder to give back. For example: "Join
            #tech voice chat for weekly meeting."
    """
    def __init__(
        self,
        reminder_id: int = 0,
        author_user_id: int = 0,
        channel_id: int = 0,
        recurrence_type: str = "N",
        next_occurrence_time: int = 0,
        expiration_time: int = 0,
        content: str = ""
    ):
        """Initialize this Reminder.

        Set the members of this Reminder to defaults or passed in parameters.

        Args:
            self: This Reminder
            reminder_id: What to initialize self.reminder_id as
            author_user_id: What to initialize self.author_user_id as
            channel_id: What to initialize self.channel_id as
            recurrence_type: What to initialize self.recurrence_type as
            next_occurrence_time: What to initialize self.next_occurrence_time
                as
            expiration_time: What sto initialize self.expiration_time as
            content: What to initialize self.content as
        """
        self.reminder_id = reminder_id
        self.author_user_id = author_user_id
        self.channel_id = channel_id
        self.recurrence_type = recurrence_type
        self.next_occurrence_time = next_occurrence_time
        self.expiration_time = expiration_time
        self.content = content

    def from_tuple(self, source: tuple) -> None:
        """Read the elements of a tuple into this Reminder.

        Overwrite the members of this Reminder with the elements of source.
        Will throw an error if the size of source was too small.

        Args:
            self: This Reminder
            source: The tuple to read from
        """
        self.reminder_id = source[0]
        self.author_user_id = source[1]
        self.channel_id = source[2]
        self.recurrence_type = source[3]
        self.next_occurrence_time = source[4]
        self.expiration_time = source[5]
        self.content = source[6]

    def to_str(self, bot: discord.Bot) -> str:
        """Convert the data in this Reminder to an human-readable string.

        Make a string including each member of this Reminder, formatted in an
        easy, human-readable way for Discord.

        Args:
            self: This Reminder
            bot: A bot instance to use to be able to search for channels

        Returns:
            A string representing this Reminder.
        """
        string = f"Reminder ID: `{self.reminder_id}`"

        string += f"\nAuthor: <@{self.author_user_id}>"

        string += "\nChannel: "
        channel = bot.get_channel(self.channel_id)
        guild = get_guild_for_channel_id(bot, self.channel_id)
        if guild is not None:
            string += f"`#{channel.name}` in Guild `{channel.guild.name}`"
        elif isinstance(channel, discord.abc.PrivateChannel):
            string += f"Private channel, ID `{self.channel_id}`"
        else:
            string += f"Unknown channel, ID `{self.channel_id}`"

        string += "\nRepeats: `"
        recurrance_type_to_str_dict = {
            "N" : "never",
            "D" : "daily",
            "W" : "weekly",
            "M" : "monthly",
            "Y" : "yearly",
        }
        string += recurrance_type_to_str_dict[self.recurrence_type]

        string += "`\nNext occurs: `"
        struct_time = time.localtime(float(self.next_occurrence_time))
        string += f"{time.strftime(TIME_FORMAT, struct_time)}"

        string += "`\nExpires: `"
        struct_time = time.localtime(float(self.expiration_time))
        string += f"{time.strftime(TIME_FORMAT, struct_time)}"

        string += f"`\nContent: `{self.content}`"

        return string

    def is_safe(self) -> bool:
        """Assert whether this Reminder is database-safe.

        Return whether the members of this Reminder have the expected types and
        value ranges to be injected into SQL statements used by this Reminder.
        This is to prevent SQL injection attacks and enforce some consitency in
        the database.

        Args:
            self: This Reminder

        Returns:
            Whether this Reminder's members are database-safe.
        """
        return isinstance(self.reminder_id, int) and \
            isinstance(self.author_user_id, int) and \
            isinstance(self.channel_id, int) and \
            isinstance(self.recurrence_type, str) and \
            isinstance(self.next_occurrence_time, int) and \
            isinstance(self.expiration_time, int) and \
            isinstance(self.content, str) and \
            self.recurrence_type in ("N", "D", "W", "M", "Y") and \
            self.next_occurrence_time >= 0 and \
            self.next_occurrence_time <= 4294967295 and \
            self.expiration_time >= 0 and \
            self.expiration_time <= 4294967295 and \
            len(self.content) <= 200

    def create(self) -> bool:
        """Create this Reminder instance in the database.

        Create a new row with the members of this Reminder (besides reminder_id,
        which will be auto-generated to be unique by the SQLite) in the
        reminders database.

        Args:
            self: This Reminder

        Returns:
            Whether the operation was successful. It may not be, for example,
            if the connection to the database, or the database itself, is not
            found or is faulty. Or, if your parameters were unsafe.
        """
        # Check safety of parameters
        if self.is_safe() is False:
            return False

        # Execute SQL query
        # If no reminder_id is specified, SQLite will automatically generate a
        # unique reminder_id, see https://www.sqlite.org/autoinc.html
        return sqlite.run(
            file_name = DB_FILE_NAME,
            query = f"INSERT INTO {DB_TABLE_NAME} VALUES "\
                + "(" \
                +     "NULL,"\
                +     f"{self.author_user_id}," \
                +     f"{self.channel_id}," \
                +     "?," \
                +     f"{self.next_occurrence_time}," \
                +     f"{self.expiration_time}," \
                +     "?" \
                + ")",
            query_parameters = (self.recurrence_type, self.content),
            commit = True
        ).success

    def update(self, column_name: str) -> bool:
        """Overwrite column_name's value with this Reminder's equivalent member.

        Overwrite the current value of what's at column: column_name, row:
        self.reminder_id, with the equivalent member from this Reminder.

        Args:
            self: This Reminder
            column_name: The name of the column whose value to overwrite

        Returns:
            Whether the operation was successful. It may not be, for example,
            if the connection to the database, or the database itself, is not
            found or is faulty. Or, if your parameters would be unsafe or the
            reminder to update doesn't exist anymore.
        """
        # Check safety of parameters
        if self.is_safe() is False:
            return False

        # Get member to modify
        name_to_value_dict = {
            "repeats": ("recurrance_type", self.recurrence_type),
            "start_time": ("next_occurrence_time", self.next_occurrence_time),
            "end_time": ("expiration_time", self.expiration_time),
            "content": ("content", self.content)
        }
        if column_name not in name_to_value_dict:
            return False
        new_value = name_to_value_dict[column_name][1]
        column_name = name_to_value_dict[column_name][0]

        # Execute SQL query
        return sqlite.run(
            file_name = DB_FILE_NAME,
            query = f"UPDATE {DB_TABLE_NAME} SET {column_name}=" \
                + f"{'?' if isinstance(new_value, str) else new_value} " \
                + f"WHERE reminder_id={self.reminder_id}",
            query_parameters = (new_value,) if isinstance(new_value, str) \
                else (),
            commit = True
        ).success

    def read(self, reminder_id: int) -> bool:
        """Copy Reminder matching reminder_id from database.

        Try to find the row in the table outstanding_reminders matching
        reminder_id for the reminders database. If it exists, overwrite the
        members of this Reminder with its data entries.

        Args:
            self: This Reminder
            reminder_id: The unique identifier of the reminder to copy

        Returns:
            Whether the operation was successful. It may not be, for example,
            if the connection to the database, or the database itself, is not
            found or is faulty. Or, a reminder with reminder_id simply does not
            exist.
        """
        # Check safety of parameters
        if not isinstance(reminder_id, int):
            return False

        # Execute SQL query
        status = sqlite.run(
            file_name = DB_FILE_NAME,
            query = f"SELECT * FROM {DB_TABLE_NAME} WHERE reminder_id=" \
                + f"{reminder_id}",
            query_parameters = (),
            commit = False
        )

        # If there was no match, return failure and don't change this
        # Reminder's members
        if status.success is False or status.result == []:
            return False

        self.from_tuple(status.result[0])
        return True

    def delete(self, reminder_id: int) -> bool:
        """Delete the Reminder matching reminder_id from the database.

        Find the row in the database matching reminder_id and delete it in its
        entirety.

        Args:
            self: This Reminder
            reminder_id: The unique identifier of the reminder to delete

        Returns:
            Whether the operation was successful. It may not be, for example,
            if the connection to the database, or the database itself, is not
            found or is faulty. Or, a reminder with reminder_id simply does not
            exist.
        """
        # Check safety of parameters
        if not isinstance(reminder_id, int):
            return False

        # Execute SQL query
        return sqlite.run(
            file_name = DB_FILE_NAME,
            query = f"DELETE FROM {DB_TABLE_NAME} WHERE reminder_id="\
                + f"{reminder_id}",
            query_parameters = (),
            commit = True
        ).success



# Create reminder slash command group
reminder_slash_command_group = discord.SlashCommandGroup(
    checks = [ctx_check.assert_author_is_allowed_to_call_command],
    #default_member_permissions = default,
    description = "Reminding commands",
    #description_localizations = default,
    #guild_ids = default,
    guild_only = False,
    name = "reminder",
    #name_localizations = default,
    #nsfw = default,
    #parent = default
)



@reminder_slash_command_group.command(
    name="add",
    description="Add a reminder for yourself to print later in this channel.",
)
async def reminder_add(
    ctx,
    repeats: discord.Option(
        str,
        description="On what increment this reminder should repeat.",
        choices=["never", "daily", "weekly", "monthly", "yearly"]
    ),
    start_time: discord.Option(
        str,
        description=f"When to first remind. {BOT_OWNER_TIMEZONE}. " \
            + "Ex: 2023NOV09 17:00.",
        max_length=len(TIME_FORMAT_EXAMPLE)
    ),
    end_time: discord.Option(
        str,
        description=f"When to stop reminder. {BOT_OWNER_TIMEZONE}. " \
            + "Ex: 2023NOV10 17:00.",
        max_length=len(TIME_FORMAT_EXAMPLE)
    ),
    content: discord.Option(
        str,
        description="What you wish to be reminded of.",
        max_length=200
    )
):
    """Tell bot to add a new reminder for you.

    Add a new reminder that will @ mention you in the channel you created it.

    Args:
        ctx: The context this SlashCommand was called under
        repeats: On what increment this reminder will repeat.
        start_time: A TIME_FORMAT formatted string of when this reminder should
            first be issued. Assumes bot owner's timezone.
        end_time: A TIME_FORMAT formatted string of when this reminder
            will be deleted and never issued again. Assumes bot owner's
            timezone.
        content: What to remind yourself of or to do.
    """
    # Determine if the author's arguments are valid
    err_msg = ""
    start = None
    end = None
    try:
        start = time.strptime(start_time, TIME_FORMAT)
        end = time.strptime(end_time, TIME_FORMAT)
        now = time.localtime()
        if time.mktime(now) > time.mktime(start):
            err_msg += "\nPlease use a start_time later than the current time."
        if time.mktime(start) > time.mktime(end):
            err_msg += "\nPlease use an end_time later than the start_time."
    except ValueError:
        err_msg += "Invalid format for start_time or end_time." \
            + f"\nPlease use the format {TIME_FORMAT_EXAMPLE} ((Y)ear, " \
            + "abbreviated (M)onth name, (D)ay, (H)our, (M)inute)."

    # If the author's arguments were invalid,
    # give them verbose error messages and an example to help them
    if err_msg != "":
        err_msg += "\nHere's an example command." \
            + "\nRemind me to pick up John the next 2 weeks." \
            + "\n`/reminder add repeats: weekly start_time: 2023NOV09 17:00 "\
            + "end_time: 2023NOV16 17:00 content: Pick up John.`"
        await ctx.respond(ephemeral=True, content=err_msg)
        return False

    # If we got here, the arguments are valid and safe to act upon
    # Create the reminder, save it, give the author details

    # Create reminder
    reminder = Reminder(
        reminder_id = 0,
        author_user_id = ctx.author.id,
        channel_id = ctx.channel.id,
        recurrence_type = repeats[0].upper(),
        next_occurrence_time = int(time.mktime(start)),
        expiration_time = int(time.mktime(end)),
        content = content
    )

    # Create reminder
    if reminder.create() is False:
        await ctx.respond(
            ephemeral=True,
            content="Encountered internal issue creating new reminder for you."
        )
        return True

    # Get its auto-generated ROWID
    # ... see stackoverflow:
    # how-to-retrieve-the-last-autoincremented-id-from-a-sqlite-table
    sqlite_response = sqlite.run(
        file_name = DB_FILE_NAME,
        query = "SELECT last_insert_rowid()",
        query_parameters = (),
        commit = False
    )
    if sqlite_response.success is False:
        await ctx.respond(
            ephemeral=True,
            content="Your reminder was created, but there was an internal " \
                + "issue getting the ID of your new reminder for you."
        )
        return True
    reminder.reminder_id = sqlite_response.result[0][0]

    # Tell author their reminder was created, other details
    await ctx.respond(
        ephemeral=True,
        content="Created a reminder for you." \
            + "\n" \
            + "\nPlease keep in mind, I will @mention you each time this " \
            + "reminder occurs, and send the reminder via a public message " \
            + "this channel." \
            + "\nWhen a reminder is deleted, its ID may be reused." \
            + "\nThe only people that can see the contents of this reminder " \
            + "are you and admins in the guild you created it until it " \
            + "triggers or is deleted." \
            + "\nPlease delete/modify this reminder if that doesn't sit well " \
            + "with you." \
            + "\nDiscord may delete this message next time you close it."
            + "\n" \
            + "\n" + reminder.to_str(bot=ctx.bot)
    )
    return True



@reminder_slash_command_group.command(
    name="remove",
    description="Remove a reminder."
)
async def reminder_remove(
    ctx,
    reminder_id: discord.Option(
        int,
        description="The unique identifier of the reminder to remove."
    )
):
    """Tell bot to remove an existing reminder for you.

    Remove an existing reminder. Only the author of the reminder and admins are
    allowed to do this.

    Args:
        ctx: The context this SlashCommand was called under
        reminder_id: The unique identifier of the reminder to remove.
    """
    # Determine if the author's arguments are valid
    err_msg = ""
    reminder = Reminder()
    user_permission = user_perm.UserPermission(ctx)
    if reminder.read(reminder_id) is False:
        err_msg += f"Could not find reminder with reminder ID `{reminder_id}`."
    elif reminder.author_user_id != ctx.author.id and \
        not(user_permission.is_admin and ctx.guild.id == \
            get_guild_for_channel_id(ctx.bot, reminder.channel_id).id):
        err_msg += "\nOnly the author of a reminder or an admin in the " \
            "guild it was created for can remove a reminder."

    # If the author's arguments were invalid,
    # give them verbose error messages and an example to help them
    if err_msg != "":
        err_msg += "\nHere's an example command." \
            + "\nRemove my reminder to pick up John." \
            + "\n`/reminder remove reminder_id: 5`."
        await ctx.respond(ephemeral=True, content=err_msg)
        return False

    # If we got here, the arguments are valid and safe to act upon
    # Delete this reminder
    if reminder.delete(reminder_id) is False:
        await ctx.respond(
            ephemeral=True,
            content="Encountered internal issue deleting reminder " \
                + "{reminder_id} for you."
        )
        return True

    await ctx.respond(
        ephemeral=True,
        content="Deleted reminder." \
            + "\n" \
            + "\n" + reminder.to_str(bot=ctx.bot)
    )
    return True



@reminder_slash_command_group.command(
    name="modify",
    description="Modify a reminder."
)
async def reminder_modify(
    ctx,
    reminder_id: discord.Option(
        int,
        description="The unique identifier of the reminder to modify."
    ),
    field: discord.Option(
        str,
        description="Which part of the reminder to modify.",
        choices=["repeats", "start_time", "end_time", "content"]
    ),
    new_value: discord.Option(
        str,
        description="The new value for the field you chose.",
        max_length=200
    )
):
    """Tell bot to modify a field of an existing reminder for you.

    Modify an existing reminder. Only the author of the reminder is allowed to
    do this.

    Args:
        ctx: The context this SlashCommand was called under
        reminder_id: The unique identifier of the reminder to modify
        field: What part of the reminder to modify
        new_value: What to modify that part of the reminder to
    """
    # Determine if the author's arguments are valid
    err_msg = ""
    reminder = Reminder()
    if reminder.read(reminder_id) is False:
        err_msg += f"Could not find reminder with reminder ID `{reminder_id}`."
    elif reminder.author_user_id != ctx.author.id:
        err_msg += "\nYou may not modify reminders you did not author."

    if field == "repeats":
        if new_value in ("never", "daily", "weekly", "monthly", "yearly"):
            reminder.recurrence_type = new_value[0].upper()
        else:
            err_msg += "\nFor 'repeats', new_value must be either never, " \
                + "daily, weekly, monthly, or yearly."
    elif field in ("start_time", "end_time"):
        try:
            new_time = time.strptime(new_value, TIME_FORMAT)
            # Do not allow a time from the past
            if time.mktime(new_time) < time.time():
                raise ValueError
            if field == "start_time":
                # Do not allow start_time > end_time
                if time.mktime(new_time) > reminder.expiration_time:
                    raise ValueError
                reminder.next_occurrence_time = time.mktime(new_time)
            elif field == "end_time":
                # Do not allow end_time < start_time
                if time.mktime(new_time) < reminder.next_occurrence_time:
                    raise ValueError
                reminder.expiration_time = time.mktime(new_time)
        except ValueError:
            err_msg += "\nFor 'start_time' or 'end_time', new_value should " \
                + "follow the same format as when it was created: " \
                + "{TIME_FORMAT_EXAMPLE}."
    elif field == "content":
        reminder.content = new_value

    # If the author's arguments were invalid,
    # give them verbose error messages and an example to help them
    if err_msg != "":
        err_msg += "\nHere's an example command." \
            + "\nModify my reminder to pick up John, I mispelled their name." \
            + "\n`/reminder modify reminder_id: 5 field: content new_value: " \
            + "Pick up Jahn.`."
        await ctx.respond(ephemeral=True, content=err_msg)
        return False

    # If we got here, the arguments are valid and safe to act upon
    # Save the changes
    if reminder.update(column_name=field) is False:
        await ctx.respond(
            ephemeral=True,
            content="There was an internal error saving your modifications."
        )
        return True

    await ctx.respond(
        ephemeral=True,
        content="Changed reminder, this is how it looks now." \
            + "\n" \
            + "\n" + reminder.to_str(bot=ctx.bot)
    )
    return True



@reminder_slash_command_group.command(
    name="list",
    description="List reminders you can view (yours and users you admin here)."
)
async def reminder_list(ctx):
    """Tell bot to list reminders.

    Tell the bot to give you a list and details of all its reminders you are
    allowed to see. You are allowed to see all reminders you created, and all
    reminders created in this guild if you are an admin of this bot in it.

    Args:
        ctx: The context this SlashCommand was called under
    """
    # Run SQL query
    # NOTE: This query can be optimized by introducing a guild_id column to the
    # database table, but this is just a read, not a write, so I wasn't too
    # concerned about speed
    sqlite_response = sqlite.run(
        file_name = DB_FILE_NAME,
        query = f"SELECT * FROM {DB_TABLE_NAME}",
        query_parameters = (),
        commit = False
    )

    # Tell author if SQL query failed
    if sqlite_response.success is False:
        await ctx.respond(
            ephemeral=True,
            content="There was an internal error getting all the reminders."
        )
        return True

    # Make a list of strings, each list element afer the 1st representing a
    # Reminder the author is allowed to view
    page_list = ["Summary:" \
        + "\n`Reminder ID: First 50 characters of content`"]
    user_permission = user_perm.UserPermission(ctx)
    for result in sqlite_response.result:
        # Parse reminder from SQL tuple
        reminder = Reminder()
        reminder.from_tuple(result)
        # Omit a reminder from the list if the author is not allowed to view it
        if reminder.author_user_id != ctx.author.id or \
            not(user_permission.is_admin and ctx.guild.id == \
                get_guild_for_channel_id(ctx.bot, reminder.channel_id).id):
            continue
        # Append reminder to summary and overall list
        page_list[0] += f"\n`{reminder.reminder_id}: {reminder.content[:49]}`"
        page_list.append(reminder.to_str(bot=ctx.bot))

    # If the pages to display is only an empty summary, there was nothing found
    # the author was allowed to view
    if len(page_list) == 1:
        await ctx.respond(
            ephemeral=True,
            content="I could not find any reminders you are allowed to view." \
                + "You are only allowed to view reminders you authored or " \
                + "that were created in this guild, if you're an admin in it."
        )
        return True

    # Return a neat page view of the reminders allowed to be viewed
    paginator = pages.Paginator(pages=page_list, loop_pages=False)
    await paginator.respond(ctx.interaction, ephemeral=True)
    return True



class ReminderCog(commands.Cog):
    """Define an instance of a Cog to check the reminder queue every minute.

    Define an instance of a Cog, specifically to hold a task to execute a
    function to check for and execute all outstanding reminders every minute.

    Attributes:
        bot: A bot instance to get required information to issue a reminder from
        send_all_outstanding_reminders: A task to send outstanding reminders
    """
    def __init__(self, bot: discord.Bot):
        """Initialize this ReminderCog.

        Set the members of this ReminderCog to passed in parameters and start
        task to dispatch outstanidng reminders.

        Args:
            self: This ReminderCog
            bot: A bot to get required information to issue a reminder from
        """
        assert bot.is_ready()
        self.bot = bot
        self.send_all_outstanding_reminders.start()

    @tasks.loop(minutes=1.0)
    async def send_all_outstanding_reminders(self) -> None:
        """Send all outstanding reminders in the channels they were created in.

        Get all reminders with next_occurrence_time greater than the current
        epoch delta. For each, while their next_occurrence_time is still greater
        than the current epoch delta, send an @mention to their original author,
        with content, in the channel matching channel_id. Calculate the next
        next_occurrence_time based on recurrence_type. If the next
        next_occurrence_time would be greater than expiration_time, or the
        reminder is set to never reoccur, remove it from the database.
        Otherwise, update its database entry with the new next_occurrence_time.

        Args:
            self: This ReminderCog
        """
        # Get current time
        now = time.localtime()

        # Get all reminders that must be dispatched
        sqlite_response = sqlite.run(
            file_name = DB_FILE_NAME,
            query = f"SELECT * FROM {DB_TABLE_NAME} WHERE "\
                + f"next_occurrence_time<={time.mktime(now)}",
            query_parameters = (),
            commit = False
        )

        # Exit early if SQL query failed
        if sqlite_response.success is False:
            print("WARNING: SQL query to get reminders failed.")
            return

        # For each outstanding reminder...
        for result in sqlite_response.result:
            # Convert tuple into class
            reminder = Reminder()
            reminder.from_tuple(result)

            # Set variable for terminating following while loop early if needed
            reminder_is_deleted = False

            # Until the reminder is deleted or its next_occurrence time is
            # greater than the current time...
            while reminder.next_occurrence_time <= time.mktime(now) and \
                reminder_is_deleted is False:
                # Convert reminder.next_occurrence_time to other formats
                next_time = reminder.next_occurrence_time
                next_time_struct = time.localtime(next_time)
                next_date_time = datetime.datetime(
                    year = next_time_struct.tm_year,
                    month = next_time_struct.tm_mon,
                    day = next_time_struct.tm_mday,
                    hour = next_time_struct.tm_hour,
                    minute = next_time_struct.tm_min,
                    second = 0,
                    microsecond = 0,
                    tzinfo = None
                )

                # Send outstanding reminder if possible
                channel = self.bot.get_channel(reminder.channel_id)
                if channel is None:
                    print(f"WARNING: reminder {reminder.reminder_id}'s " \
                        + "channel couldn't be found, so its overdue " \
                        + "reminder wasn't sent.")
                else:
                    await channel.send(f"<@{reminder.author_user_id}>, "
                        + "I have a reminder for you from " \
                        + f"{time.strftime(TIME_FORMAT, next_time_struct)}." \
                        + f"\n{reminder.content}"
                    )

                # If the reminder occurs every day...
                if reminder.recurrence_type == "D":
                    # The next day in seconds is...
                    # 24 hours/day * 60 minutes/hour * 60 seconds/minute
                    next_time += (24 * 60 * 60)
                # If the reminder occurs every week...
                elif reminder.recurrence_type == "W":
                    # The next week in seconds is...
                    # 7 days/week * 24 hours/day * 60 minutes/hour *
                    # 60 seconds/minute
                    next_time += (7 * 24 * 60 * 60)
                # If the reminder occurs every month...
                elif reminder.recurrence_type == "M":
                    # Same day on the next month is non-constant seconds away,
                    # let dateutil library handle time difference calculations
                    next_date_time = next_date_time + relativedelta(months=+1)
                    next_time = next_date_time.timestamp()
                # If the reminder occurs every month...
                elif reminder.recurrence_type == "Y":
                    # Same day on the next year is non-constant seconds away,
                    # let dateutil library handle time difference calculations
                    next_date_time = next_date_time + relativedelta(years=+1)
                    next_time = next_date_time.timestamp()

                # If the reminder is set to never occur again, or next_time
                # is after expiration_time, remove the reminder, otherwise
                # set next_occurrence_time to next_time
                if reminder.recurrence_type == "N" or \
                    next_time >= reminder.expiration_time:
                    # Stop the loop
                    reminder_is_deleted = True
                    # Update table
                    if reminder.delete(reminder.reminder_id) is False:
                        print("WARNING: There was an error deleting reminder " \
                            + f"{reminder.reminder_id}")
                else:
                    # Execute SQL query
                    # (in faster/more way than reminder.save())
                    write_status = sqlite.run(
                        file_name = DB_FILE_NAME,
                        query = f"UPDATE {DB_TABLE_NAME} SET " \
                            + f"next_occurrence_time={next_time} WHERE " \
                            + f"reminder_id={reminder.reminder_id}",
                        query_parameters = (),
                        commit = True
                    )

                    # Check query status
                    if write_status.success is False:
                        print("WARNING: There was an error updating the " \
                            + "next_occrance_time of the reminder " \
                            + f"{reminder.reminder_id}.")
