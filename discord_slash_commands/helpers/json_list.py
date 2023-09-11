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

# To be usable by JSONList, a list_type_instance must have (and redefine) the functions defined by this purely virtual type
class JSONListItem:
    # Convert member variables into dict
    def from_dict(self, dictionary: dict, optimize_for_space: bool = False) -> None:
        raise NotImplementedError

    # Convert dict into member variables
    def to_dict(self, optimize_for_space: bool = False) -> dict:
        raise NotImplementedError

    # Return a copy of this JSTONListItem (return by value instead of by reference)
    def copy(self):
        raise NotImplementedError
    

# TODO: Can 2 processes having the same file open cause problems? Will it happen frequently enough I care?

# Define a list that is also written to persistent memory via JSON file whenever it is updated
class JSONList:
    def __init__(
        self,
        file_directory: str,
        file_name: str,
        list_type_instance: JSONListItem,
        max_file_size_in_bytes: int = 50000
    ):
        # The directory to of the file to read from and write to
        self.file_directory = file_directory
        # The name of the file to read from and write to
        self.file_name = file_name
        # The concatenation of self.directory and self.file_name
        self.file_path = f"{self.file_directory}/{self.file_name}"
        # The timestamp of when the file and memory were last synced
        self.last_sync = 0
        # The contents of self.json_file are expected to be a list of dicts
        self.list = []
        # Each dict within the list will define the members of a custom class, and this is how we know the type of the custom class
        self.list_type_instance = list_type_instance
        # Keep a max file size to keep bloat on the bot's computer in-check
        self.max_file_size_in_bytes = max_file_size_in_bytes
        # Populate self.list and self.list_type_instance
        self.read()

    # TODO: comment
    def file_size_is_too_big(self, new_file_size_in_bytes: int):
        # Check if the file size is at or near threshold
        if new_file_size_in_bytes * 0.75 > self.max_file_size_in_bytes:
            # Give the bot owner a warning with possible solutions
            print(f"{self.file_path} is full or near full, at {new_file_size_in_bytes} bytes of {self.max_file_size_in_bytes} max bytes.")
            print(f"Please pause or kill the bot and do one of these 3 options:")
            print(f" 1. Make a backup and manually remove uneeded info")
            print(f" 2. Increase the max file size")
            print(f" 3. Use the optimized versions of to_dict and from_dict methods")
            if file_size_in_bytes > self.max_file_size_in_bytes:
                # Refuse to read a file bigger than self.max_file_size_in_bytes
                return True
        return False

    # Read the contents of self.file_name (should be a list of dicts)
    # TODO: check directory exists
    def read(self) -> bool:
        # Instantiate local variables
        file_handle = None
        list_of_dict = []

        # Try to create a file for self.file_path
        try:
            file_handle = open(self.file_path, "x")
        # self.file_path already exists, try to read it
        except FileExistsError:
            # Make sure this read isn't too big
            file_size_in_bytes = os.path.getsize(self.file_path)
            if self.file_size_is_too_big(file_size_in_bytes):
                return False

            # Open self.file_path for reading
            file_handle = open(self.file_path, "r")

            # Try decoding contents of JSON file
            try:
                list_of_dict = json.load(file_handle)
            # There was an error parsing the contents of the JSON file
            except json.JSONDecodeError:
                # Close file
                print(f"{self.file_path} exists, but there was an error parsing it as JSON.")
                file_handle.close()
                backup_file_path = f'{self.file_directory}/{time.strftime("%Y.%m.%d-%I:%M", time.localtime())}_{self.file_name}'

                # Try to make backup of file before overwriting it
                try:
                    os.rename(self.file_path, backup_file_path)
                    print(f"Moved {self.file_path} to {backup_file_path}.")
                # There was an error moving the old contents to a backup file, just try to remove it
                except OSError:
                    print(f"Failed to move {self.file_path} to {backup_file_path}.")
                    print(f"Will delete and make a new empty {self.file_path}.")
                    os.path.remove(self.file_path)

                # Make a new fresh file, fill it with an empty array
                file_handle = open(self.file_path, "w")
                json.dump(result, file_handle)

        # Close file, log time of read
        file_handle.close()
        self.last_sync = os.path.getmtime(self.file_path)

        # Parse list of dict from JSON into a list of classes
        self.list = []
        for dictionary in list_of_dict:
            self.list_type_instance.from_dict(dictionary)
            self.list.append(self.list_type_instance.copy())

        # The read did its best and wasn't denied
        return True

    # Save contents to self.file_path (should save a list of dicts)
    def write(self) -> True:
        # Create a list of dicts to save to self.file_path
        list_of_dict = []
        for list_item in self.list:
            list_of_dict.append(list_item.to_dict())

        # Get the file size of the write
        json_dump = json.dumps(list_of_dict)
        if self.file_size_is_too_big(len(json_dump)):
            return False

        # Open self.file_path for writing, if it doesn't exist this function makes one, write to it
        file_handle = open(self.file_path, "w")
        file_handle.write(json_dump)

        # Close file, log time of write
        file_handle.close()
        self.last_sync = os.path.getmtime(self.file_path)

        # The write did its best and wasn't denied
        return True

    # Return the index of the first self.list item that makes search_function return True
    def get_list_item_index(self, search_function, search_match) -> int:
        for i in range(self.list):
            if search_function(self.list[i], search_match) == True:
                return i
        return -1
        
    # Return whether the contents of self.file_path are newer than that of memory, possible in multi-threaded situations
    def is_desynced(self) -> bool:
        try:
            last_modified = os.path.getmtime(self.file_path)
        except OSError:
            return True
        return last_modified > self.last_sync

    # If the contents of memory are older than the contents of self.file_path, overwrite memory with the contents of self.file_path
    # TODO: In (rare, but less rare the bigger the files get) multi-threaded cases, it is possible
    #       between a self.sync() and self.write() for the contents of self.file_path to get overwritten to by a different thread.
    #       That means in small time windows, different threads can overwrite each other's changes to the same file.
    #       This is probably a common problem, maybe there's a library to help me?
    def sync(self) -> bool:
        if self.is_desynced():
            return self.read()
        return False
