"""PyCord.SlashCommand for setting reminders.

This file defines slash commands for letting someone create, modify, or delete a
reminder, that may trigger once or multiple times later in guild or DM channel.
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

#==============================================================================#
# Define underlying structure                                                  #
#==============================================================================#

FILE_NAME = "reminders"
TABLE_NAME = "outstanding_reminders"



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
            knowing who @ mention with the reminder. For example: 7702529056.
        channel_id: The ID of the Discord channel where this reminder was
            issued. For knowing where to put the message containing the
            reminder. For example: 49012672219.
        recurrance_type: Whether this this reminder should trigger again
            (N)ever, (D)aily, (M)onthly, or (Y)early. For example: "N".
        next_occurance_time: The time this reminder should next be sent
            out. Measured in seconds since the last epoch. For exmaple: 1000.
        expiration_time: The time after which this reminder should expire and
            never occur again. Measured in seconds since the last epoch. For
            example: 20000.
        content: The content of the reminder to give back. For example: "Join
            #tech voice chat for weekly meeting."
    """
    def __init__(
        self,
        reminder_id: int = 0,
        author_user_id: int = 0,
        channel_id: int = 0,
        recurrance_type: str = "N",
        next_occurrance_time: int = 0,
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
            recurrance_type: What to initialize self.recurrance_type as
            next_occurance_time: What to initialize self.next_occurance_time as
            expiration_time: What to initialize self.expiration_time as
            content: What to initialize self.content as
        """
        self.reminder_id = reminder_id
        self.author_user_id = author_user_id
        self.channel_id = channel_id
        self.recurrance_type = recurrance_type
        self.next_occurance_time = next_occurance_time
        self.expiration_time = expiration_time
        self.content = content

    def from_tuple(source: tuple):
        """TODO.

        TODO.

        Args:
            TODO
        """
        self.reminder_id = source[0]
        self.author_user_id = source[1]
        self.channel_id = source[2]
        self.recurrance_type = source[3]
        self.next_occurance_time = source[4]
        self.expiration_time = source[5]
        self.content = source[6]

    def save(self) -> bool:
        """Save this Reminder instance into the database.

        Insert this Reminder into the reminder database. If a Reminder with
        the same reminder_id already exists in the table, just update its
        fields to match this Reminder.

        Args:
            self: This Reminder

        Returns:
            Whether the operation was successful. It may not be, for example,
            if the connection to the database, or the database itself, is not
            found or is faulty.
        """
        # Check safety of parameters
        if not (
            (isinstance(self.reminder_id, int) or \
                isinstance(self.reminder_id, None)) and \
            isinstance(self.author_user_id, int) and \
            isinstance(self.channel_id, int) and \
            isinstance(self.recurrance_type, str) and \
            isinstance(self.next_occurance_time, int) and \
            isinstance(self.expiration_time, int) and \
            isinstance(self.content, str) and \
            self.recurrance_type in ("N", "D", "W", "M", "Y") and \
            self.next_occurance_time >= 0 and \
            self.next_occurance_time <= 4294967295 and \
            self.expiration_time >= 0 and \
            self.expiration_time <= 4294967295 and \
            len(self.content <= 200)
        ):
            return False

        # Execute SQL query
        # If no reminder_id is specified, SQLite will automatically generate a
        # unique reminder_id, see https://www.sqlite.org/autoinc.html
        return sqlite.run(
            file_name = FILE_NAME,
            query = f"INSERT INTO {TABLE_NAME} VALUES "\
                + "(" \
                +     f"{'NULL' if reminder_id is None else self.reminder_id},"\
                +     f"{self.author_user_id}," \
                +     f"{self.channel_id}," \
                +     "?," \
                +     f"{self.next_occurance_time}," \
                +     f"{self.expiration_time}" \
                +     "?," \
                + ") ON CONFLICT(reminder_id) DO UPDATE SET " \
                +     f"author_user_id={self.author_user_id}," \
                +     f"channel_id={self.channel_id}," \
                +     "recurrance_type=?," \
                +     f"next_occurrance_time={self.next_occurance_time}," \
                +     f"expiration_time={self.expiration_time}," \
                +     "content=?",
            query_parameters = (
                self.recurrance_type,
                self.content,
                self.recurrance_type,
                self.content
            ),
            commit = True
        ).success is True

    def read(self, reminder_id: int):
        """Copy Reminder matching reminder_id from database.

        Try to find the row in the table outstanding_reminders matching
        reminder_id for the reminders database. If it exists, overwrite the 
        members of this TTSUserPreference with its data entries.

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
            file_name = FILE_NAME,
            query = "SELECT author_user_id,channel_id,recurrance_type," \
                "next_occurance_time,expiration_time,content FROM" \
                + f"{TABLE_NAME} WHERE reminder_id={reminder_id}",
            query_parameters = (),
            commit = False
        )

        # If there was no match, return failure and don't change this
        # Reminder's members
        if status.success is False:
            return False

        # There was a match, overwrite this Reminder's members with values from
        # the database
        self.from_tuple(status.result[0])
        return True

    def delete(self, reminder_id: int):
        """TODO.

        TODO.

        Args:
            TODO

        Returns:
            TODO.
        """
        # Check safety of parameters
        if not isinstance(reminder_id, int):
            return False

        # Execute SQL query
        return sqlite.run(
            file_name = FILE_NAME,
            query = f"DELETE FROM {TABLE_NAME} WHERE reminder_id="\
                + f"{reminder.reminder_id}",
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



BOT_OWNER_TIMEZONE = "PST"
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
        description="When to first remind. {BOT_OWNER_TIMEZONE}. " \
            + "Format: YYYYMMMDD HH:MM.",
        max_length=len("YYYYMMMDD HH:MM")
    ),
    end_time: discord.Option(
        str,
        description="When to stop reminder. {BOT_OWNER_TIMEZONE}. " \
            + "Format: YYYYMMMDD HH:MM.",
        max_length=len("YYYYMMMDD HH:MM")
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
        start_time: A "YYYYMMMDD HH:MM" formatted string of when this reminder
            should first be issued. Assumes bot owner's timezone.
        end_time: A "YYYYMMMDD HH:MM" formatted string of when this reminder
            will be deleted and never issued again. Assumes bot owner's
            timezone.
        content: What to remind yourself of or to do.
    """
    # Determine if the author's arguments are valid
    err_msg = ""
    start = sqlite.SQLTime()
    end = sqlite.SQLTime()

    try:
        start.from_string(start_time)
        end.from_string(end_time)
    except:
        err_msg += "Invalid format for start_time or end_time." \
            + "\nPlease use the format YYYYMMMDD HH:MM, where Y represent " \
            + "year, M represents month, D represents day, H represents " \
            + "hour, and M represents minute. " \
            + "\nFor example, January 1st 2020 at 5:21 PM would be 2020JAN01 " \
            + "17:21."

    now = sqlite.SQLTime()
    now.from_struct_time()
    if now.to_epoch_delta() > start.to_epoch_delta():
        err_msg += "\nPlease use a start_time later than the current time."
    if start.to_epoch_delta() > end.to_epoch_delta():
        err_msg += "\nPlease use an end_time later than the start_time."

    # If the author's arguments were invalid,
    # give them verbose error messages and an example to help them
    if err_msg != "":
        err_msg += "\nHere's an example command." \
            + "\nRemind me to pick up John the next 2 weeks." \
            + "\n`/reminder add repeats: never start_time: 2023NOV08 14:00 " \
            + "end_time: 2023NOV20 14:00 content: Pick up John.`"
        await ctx.respond(ephemeral=True, content=err_msg)
        return False

    # If we got here, the arguments are valid and safe to act upon
    # Create the reminder, save it, give the author details

    # Create reminder
    reminder = Reminder(
        reminder_id = None,
        author_user_id = ctx.author.id,
        channel_id = ctx.channel.id,
        recurrance_type = repeats[0].upper(),
        next_occurrance_time = start.to_epoch_delta(),
        expiration_time = end.to_epoch_delta(),
        content = content
    )

    # Save reminder
    if reminder.save() is False:
        await ctx.respond(
            ephemeral=True,
            content="An internal issue ocurred creating a new reminder for you."
        )
        return True
        

    # Get its auto-generated ROWID
    # ... see stackoverflow:
    # how-to-retrieve-the-last-autoincremented-id-from-a-sqlite-table
    # TODO: does this only work for auto-increment?
    sqlite_repsonse = sqlite.run(
        file_name = FILE_NAME,
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
    reminder.reminder_id = sqlite_response.result[0]

    # Tell author their reminder was created, other details
    await ctx.respond(
        ephemeral=True,
        content="Created a reminder for you." \
            + "\nPlease keep in mind, it will @mention you each time it " \
            + "occurs, and will remind you via a public message in this " \
            + "channel. The only people that can see the contents of the " \
            + "reminder are you and the bot owner until it is printed (" \
            + "the data to make the reminder actually work needs to be " \
            + "stored somewhere!). Please delete/modify this reminder if " \
            + "that does not sit well with you." \
            + f"\nReminder ID: {reminder.id}" \
            + f"\nRepeats: {repeats}" \
            + f"\nStarts: {start_time}" \
            + f"\nEnds: {end_time}" \
            + f"\nContent: {content}" \
    )
    return True



@reminder_slash_command_group.command(
    name="remove",
    description="Remove a reminder.",
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
        err_msg += f"Could not find reminder with reminder ID {reminder_id}." \
            + "\nIt may have been deleted, or you simply typed it wrong. The " \
            + "reminder_id should be printed when you first make the " \
            + "reminder and whenever it triggers."
    elif reminder.author_user_id != ctx.author.id and \
        user_permission.is_admin is False:
        err_msg += "\nYou are not allowed to remove this reminder, because " \
            + "you are not its author nor an admin in this guild."

    # If the author's arguments were invalid,
    # give them verbose error messages and an example to help them
    if err_msg != "":
        err_msg += "\nHere's an example command." \
            + "\nRemove my reminder to pick up John." \
            + "\n`/reminder remove reminder_id: 51026717826`."
        await ctx.respond(ephemeral=True, content=err_msg)
        return False

    # If we got here, the arguments are valid and safe to act upon
    # Delete this reminder
    reminder.delete(reminder_id)
    await ctx.respond(
        ephemeral=True,
        content=f"Deleted reminder {reminder_id}."
    )
    return True



@reminder_slash_command_group.command(
    name="modify",
    description="Modify a reminder.",
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
    user_permission = user_perm.UserPermission(ctx)
    if reminder.read(reminder_id) is False:
        err_msg += f"Could not find reminder with reminder ID {reminder_id}." \
            + "\nIt may have been deleted, or you simply typed it wrong. The " \
            + "reminder id should be printed when you first make the " \
            + "reminder and whenever it triggers."
    elif reminder.author_user_id != ctx.author.id:
        err_msg += "\nYou may not modify reminders you did not author."

    if field == "repeats":
        if new_value in ("never", "daily", "weekly", "monthly", "yearly"):
            reminder.recurrance_type = new_value[0].upper()
        else:
            err_msg += "\nFor 'repeats', new_value must be either never, " \
                + "daily, weekly, monthly, or yearly."
    elif field in ("start_time", "end_time"):
        new_time = SQLTime()
        try:
            new_time.from_str(new_value)
            if field == "start_time":
                # TODO: should be less than or equal to 
                #       reminder.expiration_time, greater than current time
                reminder.next_occurance_time = new_time.to_epoch_delta()
            elif field == "end_time":
                # TODO: should be greater than or equal to 
                #       reminder.next_occurance_time, greater than current time
                reminder.expiration_time = new_time.to_epoch_delta()
        except:
            err_msg += "\nFor 'start_time' or 'end_time', new_value follow " \
                + "the format YYYYMMMDD HH:MM, where Y = year, M = month, " \
                + "D = day, H = hour, and M = minute." \
                + "\nFor example, January 1st 2020 at 5:21 PM would be " \
                + "2020JAN01 17:21."
    elif field == "content":
        reminder.content = content

    # If the author's arguments were invalid,
    # give them verbose error messages and an example to help them
    if err_msg != "":
        err_msg += "\nHere's an example command." \
            + "\nModify my reminder to pick up John, I mispelled their name." \
            + "\n`/reminder modify reminder_id: 51026717826 field: content " \
            + "new_value: Pick up Jahn.`."
        await ctx.respond(ephemeral=True, content=err_msg)
        return False

    # If we got here, the arguments are valid and safe to act upon
    # Save the changes
    if reminder.save() is False:
        await ctx.respond(
            ephemeral=True,
            content=f"There was an internal error saving your modifications."
        )
        return True

    await ctx.respond(
        ephemeral=True,
        content=f"Changed {field} for reminder {reminder_id} to {new_value}."
    )
    return True



# TODO: run this in cog in main.py that runs every minute
def send_all_outstanding_reminders(bot: discord.Bot) -> None:
    """Send all outstanding reminders in the channels they were created in.

    Get all reminders with next_occurance_time greater than the current epoch
    delta. For each, while their next_occurance_time is still greater than the
    current epoch delta, send an @mention to their original author, with
    reminder_id and content, in the channel matching channel_id. Calculate the
    next next_occurance_time based on recurrance_type. If the next 
    next_occurance_time would be greater than expiration_time, or the reminder
    is set to never reoccur, remove it from the database. Otherwise update its
    database entry with the new next_occurance_time.

    Args:
        bot: A bot context to use to get the matching channel for channel_id
    """
    # Get current time
    now = SQLTime()
    now.from_struct_time()

    # Get all reminders that must be dispatched
    sqlite_response = sqlite.run(
        file_name = FILE_NAME,
        query = f"SELECT * FROM {TABLE_NAME} WHERE"\
            + f"next_occurance_time<={now.to_epoch_delta()}",
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

        # Until the reminder is deleted or its next_occurance time is greater
        # than the current time...
        while result.next_occurance_time < now.to_epoch_delta and \
            reminder_is_deleted is False:
            # Convert reminder.next_occurance_time to SQLTime
            next_occurance_time = SQLTime()
            next_occurance_time.from_epoch_delta(reminder.next_occurance_time)

            # Send outstanding reminder if possible
            channel = bot.get_channel(reminder.channel_id)
            if channel == None:
                print(f"WARNING: reminder {reminder.reminder_id}'s channel " \
                    + "couldn't be found, so its overdue reminder wasn't sent.")
            else:
                channel.send(
                    ephemeral=False,
                    content=f"<@{reminder.author_user_id}>, I have a " \
                        + "reminder for {next_occurance_time.to_string()} "
                        + "for you." \
                        + f"\nReminder ID: {reminder.reminder_id}."
                        + f"\n{reminder.content}"
                )

            # If the reminder occurs every day...
            if reminder.reccurance_type == "D":
                # The next day in seconds is...
                # 24 hours/day * 60 minutes/hour * 60 seconds/minute
                next_occurance_time.from_epoch_delta(
                    next_occurance_time.to_epoch_delta() + (24 * 60 * 60)
                )
            # If the reminder occurs every week...
            elif reminder.recurrance_type == "W":
                # The next week in seconds is...
                # 7 days/week * 24 hours/day * 60 minutes/hour * 
                # 60 seconds/minute
                next_occurance_time.from_epoch_delta(
                    next_occurance_time.to_epoch_delta() + (7 * 24 * 60 * 60)
                )
            # If the reminder occurs every month...
            elif reminder.recurrance_type == "M":
                # The same day on the next month is non-constant seconds away.
                # Let time library handle the calculations. Simply add a month,
                # if it would overflow, and a year and wrap around.
                next_occurance_time.month += 1
                if next_occurance_time > 12:
                    next_occurance_time.year += 1
                    next_occurance_time.month = 1
            # If the reminder occurs every month...
            elif reminder.recurrance_type == "Y":
                # The same day on the next year is non-constant seconds away.
                # Let time library handle the calculations. Simply add a year.
                next_occurance_time.year += 1

            # If the reminder is set to never occur again, or the next
            # next_occurance_time is after expiration_time,
            # remove the reminder, otherwise update next_occurance_time
            if reminder.recurrance_type == "N" or \
                next_occurance_time.to_epoch_delta() >= \
                    reminder.expiration_time:
                # Stop the loop
                reminder_is_deleted = True
                # Update table
                if reminder.delete(reminder.reminder_id) is False:
                    print("WARNING: There was an error deleting reminder " \
                        + f"{reminder.reminder_id}")
            else:
                # Execute SQL query
                # (that's faster and more specific faster than reminder.save())
                write_status = sqlite.run(
                    file_name = FILE_NAME,
                    query = f"UPDATE {TABLE_NAME} SET next_occurance_time=" \
                        + "{next_occurance_time.to_epoch_delta()} " \
                        + "WHERE reminder_id={reminder.reminder_id}",
                    query_parameters = (),
                    commit = True
                )

                # Check query status
                if write_status.success == False:
                    print("WARNING: There was an error updating the " \
                        + "next_occrance_time of the reminder " \
                        + f"{reminder.reminder_id}")
