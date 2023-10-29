"""Functions for easily accessing bot internal databases.

This file defines functions for easily utilizing the sqlite3 Python library to
use SQL Lite databases. These databases are serverless and saved on the bot
owner's disk.
"""

#==============================================================================#
# Import libraries                                                             #
#==============================================================================#

# Import API for using SQLLite
import sqlite3

# Assert sqlite library works for multiple threads
# See https://docs.python.org/3/library/sqlite3.html#sqlite3.threadsafety
assert sqlite3.threadsafety == 3

#==============================================================================#
# Define underlying structure                                                  #
#==============================================================================#

global connection_dict
connection_dict = {}

# TODO: always check for bad return and throw values for functions
# TODO: make strings sql injection resistant
# TODO: check for database files getting too big

def add_connection(
    table_name: str,
    column_name_list: list
) -> None:
    """Create a sqlite3 connection for the file at ./db/$table_name.db.

    Create a sqlite3 connection for the file at ./db/$table_name.db. Check the
    internals of that file to make sure table_name exists in it. If it doesn't,
    create that table with the columns provided in column_name_list. Add the
    connection_dict. You should call this function in your top-level thread,
    then make new threads, so all threads use the same, multi-thread safe
    connections saved in connection_dict.

    Args:
        table_name: The name of the table to get a connection for
        column_name_list: A list of strings, where each element is the name
            of one column in the table to create or already created for
            ./db/$table_name.db
    """
    # Create connection for file_name that is multi-thread safe
    connection_dict[table_name] = sqlite3.connect(
        database=f"db/{table_name}.db",
        check_same_thread=False,
        autocommit=False
    )

    # Get cursor (iterator-like object) for the connection
    cursor = connection_dict[table_name].cursor

    # Assert the table exists within table_name's database file,
    # if not create it
    sqlite_response = cursor.execute("SELECT {table_name} FROM sqlite_master")
    if sqlite_response.fetchone() is None:
        cursor.execute(
            f"CREATE TABLE {table_name}({', '.join(column_name_list)})"
        )
    connection.commit()

def get_matches(
    table_name: str,
    match_condition: str
    column_name_list: [],
):
    """Get columns in rows matching match_condition from table_name.

    Run SELECT $column_name_list FROM $table_name WHERE $match_condition, using
    the pre-made connections in connection_dict.

    Args:
        table_name: The name of the table to want to search in. For example,
            "tts_info".
        match_condition: The SQL condition a row must meet to matching what
            you're searching for. For example, "guild_id=0,user_id=0".
        column_name_list: The rows matching match_condition might have many
            columns, this is a list of the columns from the matching rows you
            want to know the values of. For example, ["spoken_name","language"].

    Returns:
        None if a pre-existing connection could not be found for table_name or
        no matches were found. Otherwise, a list of tuples, where each list
        element coressponds to a row matching match_condition, and each tuple
        element coressponds to a column you specified in column_name_list.
    """
    # Get pre-existing connection from connection_dict, if one doesn't exist,
    # can't do the query and return failure
    connection = connection_dict[table_name]
    if connection is None:
        return None

    # Get cursor (iterator-like object) for the connection
    cursor = connection_dict[table_name].cursor

    # Run SELECT
    sqlite_response = cursor.execute(
        f"SELECT ({', '.join(column_name_list)}) " \
            + "FROM {table_name} WHERE {match_condition}"
    )
    return sqlite_response.fetchall()

def insert_rows(
    table_name: str,
    row_list: []
) -> bool:
    """Add each row in rows to the table at table_name.

    Run INSERT INTO $table_name VALUES $row, for each row in row_list, using the
    pre-made connections in connection_dict.

    Args:
        table_name: The name of the table to want to add a row to. For example,
            "tts_info".
        row: A list of tuples representing the rows you wish to add to the table
            at table_name. For example, [(0, 0, "Bill", "en"),
            (0, 1, "Pablo", "es")].

    Returns:
        Whether the operation succeeded. It will not succeed if a connection for
        table_name was not already made in connection_dict.
    """
    # Get pre-existing connection from connection_dict, if one doesn't exist,
    # can't do the query and return failure
    connection = connection_dict[table_name]
    if connection is None:
        return False

    # Get cursor (iterator-like object) for the connection
    cursor = connection_dict[table_name].cursor

    # Run INSERT
    for row in row_list:
        sqlite_response = cursor.execute(
            f"INSERT INTO {table_name} VALUES ({', '.join(row)})"
        )

    # Commit changes
    connection.commit()

    # Return success
    return True

def delete_rows(
    table_name: str,
    deletion_condition: str
) -> bool:
    """Remove rows from the table at table_name matching deletion_condition.

    Run DELETE FROM $table_name WHERE $deletion_condition, using the pre-made
    connections in connection_dict.

    Args:
        table_name: The name of the table to want to remove a row from. For
            example, "tts_info".
        match_condition: The SQL condition a row must meet to be deleted. For
            example, "guild_id=0,user_id=0".

    Returns:
        Whether the operation succeeded. It will not succeed if a connection for
        table_name was not already made in connection_dict.
    """
    # Get pre-existing connection from connection_dict, if one doesn't exist,
    # can't do the query and return failure
    connection = connection_dict[table_name]
    if connection is None:
        return False

    # Get cursor (iterator-like object) for the connection
    cursor = connection_dict[table_name].cursor

    # Run DELETE
    sqlite_response = cursor.execute(
        f"DELETE FROM {table_name} WHERE {deletion_condition})"
    )

    # Commit changes
    connection.commit()

    # Return success
    return True
