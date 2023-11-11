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

# Import Discord Python API
import discord

# TODO
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

FILE_NAME = "reminders"
TABLE_NAME = "outstanding_reminders"
TIME_FORMAT = "%Y%b%d %H:%M"



def get_guild_for_channel_id(
    bot: discord.Bot,
    channel_id: int
):
    """TODO.

    TODO.

    Args:
        TODO
    """
    channel = bot.get_channel(channel_id)
    if isinstance(channel, discord.abc.GuildChannel) or \
        isinstance(channel, discord.abc.Thread):
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
            knowing who @ mention with the reminder. For example: 7702529056.
        channel_id: The ID of the Discord channel where this reminder was
            issued. For knowing where to put the message containing the
            reminder. For example: 49012672219.
        recurrence_type: Whether this this reminder should trigger again
            (N)ever, (D)aily, (M)onthly, or (Y)early. For example: "N".
        next_occurrence_time: The time this reminder should next be sent
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
        easy, human-readable way.

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
        if guild != None:
            string += f"`#{channel.name}` in Guild `{channel.guild.name}`"
        elif (isinstance(channel, discord.abc.PrivateChannel)):
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

    def save(self, new_reminder: bool = False) -> bool:
        """Save this Reminder instance into the database.

        Insert this Reminder into the reminder database. If a Reminder with
        the same reminder_id already exists in the table, just update its
        fields to match this Reminder.

        Args:
            self: This Reminder
            new_reminder: Whether to add a new row to the database for this save
                or try to overwrite an existing row.

        Returns:
            Whether the operation was successful. It may not be, for example,
            if the connection to the database, or the database itself, is not
            found or is faulty.
        """
        # Check safety of parameters
        if not (
            isinstance(self.reminder_id, int) or \
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
        ):
            return False

        # Execute SQL query
        # If no reminder_id is specified, SQLite will automatically generate a
        # unique reminder_id, see https://www.sqlite.org/autoinc.html
        return sqlite.run(
            file_name = FILE_NAME,
            query = f"INSERT INTO {TABLE_NAME} VALUES "\
                + "(" \
                +     f"{'NULL' if new_reminder else self.reminder_id},"\
                +     f"{self.author_user_id}," \
                +     f"{self.channel_id}," \
                +     f"?," \
                +     f"{self.next_occurrence_time}," \
                +     f"{self.expiration_time}," \
                +     "?" \
                + ") ON CONFLICT(reminder_id) DO UPDATE SET " \
                +     f"author_user_id={self.author_user_id}," \
                +     f"channel_id={self.channel_id}," \
                +     f"recurrence_type=?," \
                +     f"next_occurrence_time={self.next_occurrence_time}," \
                +     f"expiration_time={self.expiration_time}," \
                +     "content=?",
            query_parameters = (
                self.recurrence_type,
                self.content,
                self.recurrence_type,
                self.content
            ),
            commit = True
        ).success is True

    def read(self, reminder_id: int):
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
            file_name = FILE_NAME,
            query = f"SELECT * FROM {TABLE_NAME} WHERE reminder_id=" \
                + f"{reminder_id}",
            query_parameters = (),
            commit = False
        )

        # If there was no match, return failure and don't change this
        # Reminder's members
        if status.success is False or status.result == []:
            return False

        # There was a match, overwrite this Reminder's members with values from
        # the database
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
            file_name = FILE_NAME,
            query = f"DELETE FROM {TABLE_NAME} WHERE reminder_id="\
                + f"{self.reminder_id}",
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
        description=f"When to first remind. {BOT_OWNER_TIMEZONE}. " \
            + "Ex: 2023NOV09 17:00.",
        max_length=len("YYYYMMMDD HH:MM")
    ),
    end_time: discord.Option(
        str,
        description=f"When to stop reminder. {BOT_OWNER_TIMEZONE}. " \
            + "Ex: 2023NOV10 17:00.",
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
    except:
        err_msg += "Invalid format for start_time or end_time." \
            + "\nPlease use the format YYYYMMMDD HH:MM ((Y)ear, abbreviated " \
            + "(M)onth name, (D)ay, (H)our, (M)inute)."

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

    # Save reminder
    if reminder.save(new_reminder=True) is False:
        await ctx.respond(
            ephemeral=True,
            content="Encountered internal issue creating new reminder for you."
        )
        return True
        
    # Get its auto-generated ROWID
    # ... see stackoverflow:
    # how-to-retrieve-the-last-autoincremented-id-from-a-sqlite-table
    sqlite_response = sqlite.run(
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
    reminder.reminder_id = sqlite_response.result[0][0]

    # Tell author their reminder was created, other details
    # Ephemeral messages can delete themselves, ctx.respond() shows what the
    # author typed, and users may disable DMs, so for getting the reminder ID
    # somewhere persistent, channel.send() is the best bet.
    await ctx.channel.send(f"Created reminder for <@{ctx.author.id}> with " \
        + f"reminder ID: `{reminder.reminder_id}`.")
    await ctx.respond(
        ephemeral=True,
        content="Created a reminder for you." \
            + "\n" \
            + "\nPlease keep in mind, I will @mention you each time this " \
            + "reminder occurs, and send the reminder via a public message " \
            + "this channel." \
            + "\nWhen this reminder is deleted, its ID may be reused." \
            + "\nThe only people that can see the contents of this reminder " \
            + "are you and the bot owner until it triggers or is deleted." \
            + "\nPlease delete/modify this reminder if that doesn't sit well " \
            + "with you." \
            + "\nDiscord may delete this message next time you close it."
            + "\n" \
            + reminder.to_str(bot=ctx.bot)
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
        not(user_permission.is_admin and \
        ctx.guild.id == get_guild_for_channel_id(bot, reminder.channel_id).id):
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
        content=f"Deleted reminder." \
            + "\n" \
            + reminder.to_str(bot=ctx.bot)
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
    user_permission = user_perm.UserPermission(ctx)
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
            if time.mktime(new_time) < time.time():
                raise ValueError
            if field == "start_time":
                if time.mktime(new_time) > reminder.expiration_time:
                    raise ValueError
                reminder.next_occurrence_time = time.mktime(new_time)
            elif field == "end_time":
                if time.mktime(new_time) < reminder.next_occurrence_time:
                    raise ValueError
                reminder.expiration_time = time.mktime(new_time)
        except:
            err_msg += "\nFor 'start_time' or 'end_time', new_value should " \
                "follow the format as when it was created: YYYYMMMDD HH:MM."
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
    if reminder.save() is False:
        await ctx.respond(
            ephemeral=True,
            content=f"There was an internal error saving your modifications."
        )
        return True

    await ctx.respond(
        ephemeral=True,
        content=f"Changed reminder, this is how it looks now." \
            + "\n" \
            + reminder.to_str(bot=ctx.bot)
    )
    return True



@reminder_slash_command_group.command(
    name="list",
    description="List reminders you are allowed to view."
)
async def reminder_view(ctx):
    """TODO.

    TODO.

    Args:
        ctx: The context this SlashCommand was called under
        reminder_id: The unique identifier of the reminder to view
    """
    # TODO: give a pagniator of all reminders you are the author of or,
    # or in a guild you admin
    
    user_permission = user_perm.UserPermission(ctx)
    sqlite_response = None
    #if user_permission.is_admin is False:
    sqlite_response = sqlite.run(
        file_name = FILE_NAME,
        query = f"SELECT * FROM {TABLE_NAME} WHERE "\
            + f"author_user_id={ctx.author.id}",
        query_parameters = (),
        commit = False
    )
    #else:
    #    sqlite_response = sqlite.run(
    #        file_name = FILE_NAME,
    #        query = f"SELECT * FROM {TABLE_NAME} WHERE "\
    #            + f"guild_id={ctx.guild.id if ctx.guild else None}",
    #        query_parameters = (),
    #        commit = False
    #    )

    if sqlite_response.success is False:
        # TODO
        ctx.respond(ephemeral=True, content="")
        return False
    if sqlite_response.result == []:
        # TODO
        ctx.respond(ephemeral=True, content="")
        return False

    reminder_list = []
    page_list = ["Table of contents:" \
        + "\n`Reminder ID: First 50 characters of content`"]
    for result in sqlite_response.result:
        reminder = Reminder()
        reminder.from_tuple(result)
        reminder_list.append(reminder)
        page_list[0] += f"\n`{reminder.reminder_id}: {reminder.content[:49]}`"
        page_list.append(reminder.to_str(bot=ctx.bot))
    
    paginator = pages.Paginator(pages=page_list, loop_pages=False)
    await paginator.respond(ctx.interaction, ephemeral=True)
    return True



class ReminderCog(commands.Cog):
    def __init__(self, bot: discord.Bot):
        """TODO.

        TODO.

        Args:
            TODO
        """
        self.bot = bot
        self.send_all_outstanding_reminders.start()

    @tasks.loop(minutes=1.0)
    async def send_all_outstanding_reminders(self) -> None:
        """Send all outstanding reminders in the channels they were created in.

        Get all reminders with next_occurrence_time greater than the current
        epoch delta. For each, while their next_occurrence_time is still greater
        than the current epoch delta, send an @mention to their original author,
        with reminder_id and content, in the channel matching channel_id.
        Calculate the next next_occurrence_time based on recurrence_type. If the
        next next_occurrence_time would be greater than expiration_time, or the
        reminder is set to never reoccur, remove it from the database. Otherwise
        update its database entry with the new next_occurrence_time.

        Args:
            TODO
        """
        # Get current time
        now = time.localtime()

        # Get all reminders that must be dispatched
        sqlite_response = sqlite.run(
            file_name = FILE_NAME,
            query = f"SELECT * FROM {TABLE_NAME} WHERE "\
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
                if channel == None:
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
                    # let datetime library handle time difference calculations
                    next_date_time = next_date_time + relativedelta(months=+1)
                    next_time = next_date_time.timestamp()
                # If the reminder occurs every month...
                elif reminder.recurrence_type == "Y":
                    # Same day on the next year is non-constant seconds away,
                    # let datetime library handle time difference calculations
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
                        file_name = FILE_NAME,
                        query = f"UPDATE {TABLE_NAME} SET " \
                            + f"next_occurrence_time={next_time} WHERE " \
                            + f"reminder_id={reminder.reminder_id}",
                        query_parameters = (),
                        commit = True
                    )

                    # Check query status
                    if write_status.success == False:
                        print("WARNING: There was an error updating the " \
                            + "next_occrance_time of the reminder " \
                            + f"{reminder.reminder_id}.")

    @send_all_outstanding_reminders.before_loop
    async def wait(self):
        """TODO.

        TODO.

        Args:
            TODO
        """
        await self.bot.wait_until_ready()
