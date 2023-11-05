"""PyCord.SlashCommand for TODO.

TODO.
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

# TODO: not measuring epoch. measuring time since epoch

class SQLTime():
    """TODO.

    TODO.

    Attributes:
        TODO
    """
    def __init__(
        self,
        year: int = 0,
        month: int = 0,
        day: int = 0,
        hour: int = 0,
        minute: int = 0,
    ):
        """TODO.

        TODO.

        Args:
            TODO
        """
        # Year integer, including century, ex. 2019
        self.year = year
        # Month integer, ex. 4 = April
        self.month = month
        # Day integer, ex. 12 = 12th
        self.day = day
        # Hour integer, military time. ex. 23 = 11PM
        self.hour = hour
        # Minute integer, ex. 31 = 31 minutes
        self.minute = minute

    def is_safe(self) -> bool:
        """TODO.

        TODO.

        Args:
            TODO

        Returns:
            TODO.
        """
        try:
            self.to_struct_time()
            return True
        except:
            return False

    def from_struct_time(self, struct_time: time.struct_time = None) -> None:
        """TODO.

        TODO.

        Args:
            TODO
        """
        # Get current local time if no time was provided
        if struct_time == None:
            struct_time = time.localtime()

        # Read members from current local time
        self.year = struct_time.tm_year
        self.month = struct_time.tm_mon
        self.day = struct_time.tm_day
        self.hour = struct_time.tm_hour
        self.minute = struct_time.tm_min

    def to_struct_time(self) -> time.struct_time:
        """TODO.

        TODO.

        Args:
            TODO

        Returns:
            TODO.
        """
        # Create struct_time from string version of this class 
        return time.strptime(self.to_str())

    def from_str(self, string: str) -> None:
        """TODO.

        TODO.

        Args:
            TODO
        """
        # Parse the passed in string into a struct_time
        struct_time = time.strptime("%Y%b%d %H:%M", string)
        self.from_struct_time(struct_time)

    def to_str(self) -> str:
        """TODO.

        TODO.

        Args:
            TODO

        Returns:
            TODO.
        """
        # See https://docs.python.org/3/library/time.html#time.strftime
        return time.strftime(
            "%Y%b%d %H:%M",
            (
                self.year,
                self.month,
                self.day,
                self.hour,
                self.minute
            )
        )

    def from_epoch(self, epoch: int) -> None:
        """TODO.

        TODO.

        Args:
            TODO
        """
        self.from_struct_time(time.localtime(epoch))

    # NOTE: According to the time module, our current epoch started on 01JAN1970
    #       and will end in 2038.
    def to_epoch(self) -> int:
        """TODO.

        TODO.

        Args:
            TODO

        Returns:
            TODO.
        """
        return time.mktime(self.to_struct_time())



class Reminder():
    """TODO.

    TODO.

    Attributes:
        TODO
    """
    def __init__(
        self,
        reminder_id: int = 0,
        author_user_id: int = 0,
        channel_id: int = 0,
        recurrance_type: str = "D",
        next_occurrance_epoch: int = 0,
        expiration_epoch: int = 0,
        content: str = ""
    ):
        """TODO.

        TODO.

        Args:
            TODO
        """
        self.reminder_id = reminder_id
        self.author_user_id = author_user_id
        self.channel_id = channel_id
        self.recurrance_type = recurrance_type
        self.next_occurrance_epoch = next_occurrance_epoch
        self.expiration_epoch = expiration_epoch
        self.content = content

    def save(self) -> bool:
        """TODO.

        TODO.

        Args:
            TODO

        Returns:
            TODO.
        """
        # Check safety of parameters
        if not (
            isinstance(self.reminder_id, int) and \
            isinstance(self.author_user_id, int) and \
            isinstance(self.channel_id, int) and \
            isinstance(self.recurrance_type, str) and \
            isinstance(self.next_occurance_epoch, int) and \
            isinstance(self.expiration_epoch, int) and \
            isinstance(self.content, str) and \
            self.recurrance_type is in ("D", "M", "Y") and \
            self.next_occurance_epoch >= 0 and \
            self.next_occurance_epoch <= 4294967295 and \
            self.expiration_epoch >= 0 and \
            self.expiration_epoch <= 4294967295 and \
            len(self.content <= 200)
        ):
            return False

        # Execute SQL query
        # TODO: reminder_id sohuld be unique and increment / be random
        return sqlite.run(
            file_name = FILE_NAME,
            query = f"INSERT INTO {TABLE_NAME} VALUES "\
                + "(" \
                +     f"{self.reminder_id}," \
                +     f"{self.author_user_id}," \
                +     f"{self.channel_id}," \
                +     "?," \
                +     "?," \
                +     f"{self.next_occurance_epoch}," \
                +     f"{self.expiration_epoch}" \
                + ")"
            query_parameters = (
                self.recurrance_type,
                self.content
            ),
            commit = True
        ).success is True



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
    description="TODO.",
)
async def reminder_add(
    ctx,
    schedule: discord.Option(
        str,
        description="TODO",
        choices=["daily", "monthly", "yearly"]
    ),
    start_time: discord.Option(
        str,
        description="TODO",
        max_length=len("YYYYMMDD HH:MM")
    ),
    end_time: discord.Option(
        str,
        description="TODO",
        max_length=len("YYYYMMDD HH:MM")
    ),
    content: discord.Option(
        str,
        description="TODO",
        max_length=200
    )
):
    """TODO.

    TODO.

    Args:
        TODO
    """
    #TODO, and also, tell user reminder id for them to reference
    ctx.respond(ephemeral=True, content="")
    return True



@reminder_slash_command_group.command(
    name="remove",
    description="TODO.",
)
async def reminder_remove(
    ctx,
    reminder_id: discord.Option(
        int,
        description="TODO"
    )
):
    """TODO.

    TODO.

    Args:
        TODO
    """
    #TODO, and also, only let the original authors or admins remove reminders
    ctx.respond(ephemeral=True, content="")
    return True



@reminder_slash_command_group.command(
    name="modify",
    description="TODO.",
)
async def reminder_remove(
    ctx,
    reminder_id: discord.Option(
        int,
        description="TODO"
    )
):
    """TODO.

    TODO.

    Args:
        TODO
    """
    #TODO, and also, only let the original authors modify reminders
    ctx.respond(ephemeral=True, content="")
    return True



@reminder_slash_command_group.command(
    name="list",
    description="TODO.",
)
async def reminder_remove(
    ctx,
    reminder_id: discord.Option(
        int,
        description="TODO"
    )
):
    """TODO.

    TODO.

    Args:
        TODO
    """
    #TODO, and also, only let admins see all reminders, might be sensitive info
    # which also means i should put a warning in the reminder creation
    ctx.respond(ephemeral=True, content="")
    return True



# TODO: run this in cog in main.py that runs every minute
def send_all_outstanding_reminders(bot: discord.Bot) -> None:
    """TODO.

    TODO.

    Args:
        TODO
    """
    # Get current time
    sql_time = SQLTime()
    sql_time.from_struct_time()

    # Get all reminders that must be dispatched
    sqlite_response = sqlite.run(
        file_name = FILE_NAME,
        query = f"SELECT * FROM {TABLE_NAME} WHERE"\
            + f"next_occurance_epoch<={sql_time.to_epoch()}"
        query_parameters = (),
        commit = False
    )

    # Exit early if SQL query failed
    if sqlite_response.success is False:
        return

    # For each outstanding reminder...
    for result in sqlite_response.result:
        # Convert tuple into class
        reminder = Reminder(
            reminder_id = result[0],
            author_user_id = result[1],
            channel_id = result[2],
            recurrance_type = result[3],
            next_occurrance_time = result[4],
            expiration_time = result[5],
            content = result[6],
        )

        # Convert reminder.next_occurance_epoch to SQLTime
        next_occurance_time = SQLTime()
        next_occurance_time.from_epoch(reminder.next_occurance_epoch)

        # Send outstanding reminder if possible
        channel = bot.get_channel(reminder.channel_id)
        if channel == None:
            print(f"Warning: reminder {reminder.reminder_id}'s channel could " \
                + "not be found, so its overdue reminder could not be sent.")
        else:
            channel.send(
                ephemeral=False,
                content=f"<@{reminder.author_user_id}>, I have a reminder " \
                    + f"at {next_occurance_time.to_string()} for you." \
                    + f"\n{reminder.content}"
            )

        # If the reminder occurs every day, increment by a day
        # The next day is in 24 hours * 60 minutes * 60 seconds
        if reminder.reccurance_type == "D":
            next_occurance_time.from_epoch(
                next_occurance_time.to_epoch() + (24 * 60 * 60)
            )
        # If the reminder occurs every month, increment by a month
        # Each month may last a different amount of seconds
        elif reminder.recurrance_type == "M":
            next_occurance_time.month += 1
            if next_occurance_time > 12:
                next_occurance_time.year += 1
                next_occurance_time.month = 0
        # If the reminder occurs every year, increment by a year
        # Each year may last a different amount of seconds
        else:
            next_occurance_time.year += 1

        # If the next_occurance_time is after expiration_time,
        # remove the reminder, otherwise update next_occurance_time
        if next_occurance_time.to_epoch() < reminder.expiration_epoch:
            sqlite.run(
                file_name = FILE_NAME,
                query = f"UPDATE {TABLE_NAME} SET " \
                    + "next_occurance_epoch={next_occurance_time.to_epoch()} " \
                    + "WHERE reminder_id={reminder.reminder_id}"
                query_parameters = (),
                commit = True
            )
        else:
            sqlite.run(
                file_name = FILE_NAME,
                query = f"DELETE FROM {TABLE_NAME} WHERE"\
                    + f"reminder_id={reminder.reminder_id}"
                query_parameters = (),
                commit = True
            )
