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
    file_name: str,
    table_name_list: list,
    column_list: list
) -> None:
    """Create a sqlite3 connection for the file at ./db/$table_name.db.

    Create a sqlite3 connection for the file at ./db/$table_name.db. Check the
    internals of that file to make sure each table_name in table_name_list
    exists in it. If it doesn't, create that table with the columns provided in
    column_list. Add the new connection to connection_dict. You should call
    this function in your top-level thread, then make new threads, so all
    threads use the same, multi-thread safe connections saved in
    connection_dict.

    Args:
        table_name: The name of the table to get a connection for
        column_list: A list of strings, where each element is the name
            of one column in the table to create or already created for
            ./db/$table_name.db
    """
    # Create connection for file_name that is multi-thread safe
    connection_dict[table_name] = sqlite3.connect(
        database=f"db/{file_name}.db",
        check_same_thread=False,
        autocommit=False
    )

    for table_name in table_name_list:
        # Get cursor (iterator-like object) for the connection
        cursor = connection_dict[table_name].cursor

        # Assert the table exists within table_name's database file,
        # if not create it
        sqlite_response = cursor.execute(
            "SELECT {table_name} FROM sqlite_master"
        )
        if sqlite_response.fetchone() is None:
            cursor.execute(
                f"CREATE TABLE {table_name}({', '.join(column_list)})"
            )
        connection.commit()



def run(
    file_name: str,
    query: str,
    query_parameters: tuple,
    commit: bool
):
    """TODO.

    TODO.

    Args:
        TODO

    Returns:
        TODO.
    """
    # Get pre-existing connection from connection_dict, if one doesn't exist,
    # can't do the query and return failure
    connection = connection_dict[file_name]
    if connection is None:
        return []

    # Get cursor (iterator-like object) for the connection
    cursor = connection_dict[file_name].cursor

    # Run query
    response = cursor.execute(query, query_parameters)

    # Commit if necessary
    if commit is True:
        connection.commit()

    # Return results
    return response.fetchall()
