"""Functions for easily accessing bot internal databases.

This file defines functions for easily utilizing the sqlite3 Python library to
use SQLite databases. These databases are serverless and saved on the bot
owner's disk.
"""

#==============================================================================#
# Import libraries                                                             #
#==============================================================================#

# Import API for using SQLite
import sqlite3

# Assert sqlite library works for multiple threads
# See https://docs.python.org/3/library/sqlite3.html#sqlite3.threadsafety
assert sqlite3.threadsafety in (1,3)

#==============================================================================#
# Define underlying structure                                                  #
#==============================================================================#

# TODO: Always check for bad return and throw values for functions.
# TODO: Check for database files getting too big.



# TODO: Assert a connection is always closed before it destructs?
def open_connection(file_name: str) -> sqlite3.Connection:
    """ Get a sqlite3.Connection to db/$file_name.db.

    Return a sqlite3.Connection to the file at db/$file_name.db that cannot be
    used in the same thread, and should be closed immediately after it's done
    being used by close_connection(...).

    Args:
        file_name: The name of database file to open, db/$filename.db

    Returns:
        A sqlite3.Connection to db/$file_name.db, if possible.
    """
    return sqlite3.connect(
        database = f"db/{file_name}.db",
        check_same_thread = True
        # TODO: Why doesn't this work? The main API page says this is a param.
        #autocommit = False
    )



def close_connection(connection: sqlite3.Connection) -> None:
    """ Close a sqlite3.Connection.

    Close a connection gotten by calling open_connection().

    Args:
        connection: The sqlite3.Connection to close
    """
    connection.close()



# NOTE: The SQL in this function is not immune to injection, please don't let
#       users use this function
def init_db(
    file_name: str,
    table_name_list: list,
    column_list: list
) -> None:
    """ Initialize db/$table_name.db if it does not already exist.

    Open db/$table_name.db, then for each table_name in table_name_list,
    if a table with that name does not exist, create it, with the columns listed
    in column_list.

    Args:
        file_name: The name of the database to open, db/$file_name.db
        table_name_list: A list of strings, where each element is a name of a
            table to enforce exists in db/$file_name.db
        column_list: A list of strings, where each element is an initializer
            of a table column. All new tables created by this function will have
            these columns created for them in db/$file_name.db.
    """
    # Create connection for file_name
    connection = open_connection(file_name)

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

    # Close connection, it is no longer needed
    close_connection(connection)



def run(
    connection: sqlite3.Connection,
    query: str,
    query_parameters: tuple,
    commit: bool
) -> list:
    """Run $query with $query_parameters on $connection, commit if $commit.

    Run $query with $query_parameters on $connection. Commit after the query if
    $commit is True.

    Args:
        connection: A connection to the database you want to run the SQL query
            on, gotten through open_connection(...)
        query: The SQL command you wish to execute
        query_parameters: The parameters that will be used in query (if you put
            user-entered info straight into query, you may be vulnerable to SQL
            injection attacks!)
        commit: Whether to commit changes after executing query

    Returns:
        A list, where each element is a query result.
    """
    # Get cursor (iterator-like object) for the connection
    cursor = connection.cursor()

    # Run query
    sqlite_response = cursor.execute(query, query_parameters)

    # Commit if necessary
    if commit is True:
        connection.commit()

    # Return results
    return sqlite_response.fetchall()
