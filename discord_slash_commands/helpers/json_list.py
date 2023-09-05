# ======================= #
# Import public libraries #
# ======================= #

# JSON reading, writing, and parsing API
import json

# Operating system API for handling things like moving files
import os

# API for handling time, such as converting timestamps to human-readable strings
import time

# =========================== #
# Define underlying structure #
# =========================== #

# TODO: Can 2 processes having the same file open cause problems? Will it happen frequently enough I care?

# Define a list that is also written to persistent memory via JSON file whenever it is updated
class JSONList:
    def __init__(
        self,
        file_name: str
    ):
        # The name of the file to read from and write to
        self.file_name = f"{file_name}.json"
        # The timestamp of when the file and memory were last synced
        self.last_sync = 0

    # Read the contents of self.file_name
    def read(self) -> list:
        # Instantiate local variables
        file_handle = None
        result = []

        # Try to create a file for self.file_name
        try:
            file_handle = open(self.file_name, "x")
        # self.file_name already exists, try to read it
        except FileExistsError:
            file_handle = open(self.file_name, "r")

            # Try decoding contents of JSON file
            try:
                result = json.load(file_handle)
            # There was an error parsing the contents of the JSON file
            except json.JSONDecodeError:
                # Close file
                print(f"{self.file_name} exists, but there was an error parsing it as JSON.")
                file_handle.close()
                backup_file_name = f'{time.strftime("%Y.%m.%d-%I:%M", time.localtime())}_{self.file_name}'

                # Try to make backup of file before overwriting it
                try:
                    os.rename(self.file_name, backup_file_name)
                    print(f"Moved {self.file_name} to {backup_file_name}.")
                # There was an error moving the old contents to a backup file, just try to remove it
                except OSError:
                    print(f"Failed to move {self.file_name} to {backup_file_name}.")
                    print(f"Will delete and make a new empty {self.file_name}.")
                    os.path.remove(self.file_name)

                # Make a new fresh file, fill it with an empty array
                file_handle = open(self.file_name, "w")
                json.dump(result, file_handle)

        # Close file, log time of read
        file_handle.close()
        self.last_sync = os.path.getmtime(self.file_name)

        # Return results
        return result

    # Save contents to self.file_name 
    def write(self, data: list) -> None:
        # Saving doesn't need nearly as much safety checking, if the file doesn't exist, it will make one
        file_handle = open(self.file_name, "w")
        json.dump(data, file_handle)
        file_handle.close()
        self.last_sync = os.path.getmtime(self.file_name)

    # See if self.file_name has been modified since the last sync, possible in multi-threaded situations
    def is_desynced(self) -> bool:
        try:
            last_modified = os.path.getmtime(self.file_name)
            return last_modified > self.last_sync
        except OSError:
            return True
