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

# TODO: Assert sqlite library works for multiple threads
# See https://docs.python.org/3/library/sqlite3.html#sqlite3.threadsafety
#assert sqlite3.threadsafety == 3

#==============================================================================#
# Define underlying structure                                                  #
#==============================================================================#

# Define a global dictionary of connections to database files, where each
# key is 'db_file', or the file name, within the path to the database file,
# in this example, ./db_file.db. The point of this is to keep Connection made
# in top level threads to be usable by spawned threads, so the sqlite3 module
# can handle each thread automatically and safely without collision.
global connection_dict
connection_dict = {}

# TODO: Always check for bad return and throw values for functions.
# TODO: Check for database files getting too big.



# NOTE: The SQL in this function is not immune to injection, please don't let
#       users use this function
def add_connection(
    file_name: str,
    table_name_list: list,
    column_list: list
) -> None:
    """Create a sqlite3.Connection for the file at ./db/$table_name.db.

    Create a sqlite3.Connection for the file at ./db/$table_name.db. Check the
    internals of that file to make sure each table_name in table_name_list
    exists in it. If it doesn't, create that table with the columns provided in
    column_list. Add the new connection to connection_dict. You should call
    this function in your top-level thread, then make new threads, so all
    threads use the same, multi-thread safe connections saved in
    connection_dict. If you need new connections after you've made multiple
    sub-threads, please restart the bot and call this function for it in your
    top level thread.

    Args:
        file_name: The name of the database file to get a connection for
        table_name_list: A list of names of tables that are supposed to exist
            within the database matching file_name
        column_list: A list of strings, where each element is an initializer
            of one column in the table to create or already created for
            ./db/$file_name.db
    """
    # Create connection for file_name that is multi-thread safe
    connection = sqlite3.connect(
        database = f"db/{file_name}.db",
        check_same_thread = False
        # TODO: Why doesn't this work? The main API page says this is a param.
        #autocommit = False
    )

    # Add or overwrite connection to connection_dict
    connection_dict[file_name] = connection

    for table_name in table_name_list:
        # Get cursor (iterator-like object) for the connection
        cursor = connection.cursor()

        # Create or assert table_name exists within file_name's database file
        sqlite_response = cursor.execute(
            f"SELECT name FROM sqlite_master WHERE name='{table_name}'"
        )
        if sqlite_response.fetchone() is None:
            cursor.execute(
                f"CREATE TABLE {table_name}({','.join(column_list)})"
            )

        # Commit changes
        connection.commit()



class Status():
    """Define a class for run to return.

    Define a class run can return that gives both the overall status and results
    of the query it executed.

    Attributes:
        success: If the query was executed and it raised no errors
        result: The SQL response of the query executed
    """
    def __init__(self, success: bool, result: list):
        """Initialize this Status.

        Set the members of this Status to the passed in or default values.

        Args:
            self: This Status
            success: What to initialize self.success as
            result: What to initialize self.result as
        """
        self.success = success
        self.result = result



def run(
    file_name: str,
    query: str,
    query_parameters: tuple,
    commit: bool
) -> Status:
    """Run query with query_parameters against the database at file_name.

    Run the SQL command query with query_parameters on the prexisting
    connection for ./db/file_name.db in connection_dict. Commit the changes
    if commit is True.

    Args:
        file_name: The file name of the database you wish to access
        query: The general SQL command you wish to execute
        query_parameters: The parameters that will be used in query (if you put
            user-entered info straight into query, you may be vulnerable to SQL
            injection attacks!)
        commit: Whether to commit changes after executing query

    Returns:
        A Status, giving both whether the query ran smoothly and what the query
        returned.
    """
    # Get pre-existing connection from connection_dict, if one doesn't exist,
    # can't do the query and return failure
    connection = connection_dict[file_name]
    if connection is None:
        return Status(False, [])

    # Get cursor (iterator-like object) for the connection
    cursor = connection_dict[file_name].cursor()

    # Run query
    sqlite_response = cursor.execute(query, query_parameters)

    # Commit if necessary
    if commit is True:
        connection.commit()

    # Return results
    return Status(True, sqlite_response.fetchall())
