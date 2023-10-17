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
    # Convert member variables to dictionary
    def to_dict(self) -> dict:
        raise NotImplementedError

    # Read member variables from dictionary
    def from_dict(self, dictionary: dict) -> None:
        raise NotImplementedError

    # Return a copy of this JSONListItem (by value, not by reference)
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
        # The directory of the JSON file to read from and write to
        self.file_directory = file_directory
        # The name of the JSON file to read from and write to
        self.file_name = file_name
        # The concatenation of self.file_directory and self.file_name
        self.file_path = f"{self.file_directory}/{self.file_name}"
        # The timestamp of when the JSON file and memory were last synced (self.read or self.write was called)
        # Measured in seconds since the last epoch, see: https://docs.python.org/3/library/time.html
        self.last_sync = 0
        # The contents of the JSON file, see if it is out of sync with the file via self.is_desynced
        # The contents of the JSON file are expected to be a list of dicts, where each dict will then be converted into the same type as self.list_type_instance
        self.list = []
        # The type of an individual self.list element
        self.list_type_instance = list_type_instance
        # The max size the JSON file is allowed to get to, to prevent bloat on the bot's computer
        self.max_file_size_in_bytes = max_file_size_in_bytes
        # Actually read the JSON file to populate self.last_sync and self.list
        self.read()

    # Return whether a length exceeds self.max_file_size_in_bytes, and give the bot's computer a warning if it's close
    def file_size_is_too_big(self, length_in_bytes: int) -> bool:
        # Check if the file size is at or near threshold
        if length_in_bytes * 0.75 > self.max_file_size_in_bytes:
            # Give the bot owner a warning with possible solutions
            print(f"{self.file_path} is full or near full, at {length_in_bytes} bytes of {self.max_file_size_in_bytes} max bytes.")
            print(f"Please consider these 3 options:")
            print(f" 1. Pause the bot, make a backup of the JSON file, manually remove uneeded info from it, unpause the bot.")
            print(f" 2. Kill the bot, increase the max file size for this JSON file, restart the bot.")
            print(f" 3. Optimize the code, such as the to_dict and from_dict methods, or use a database to store information instead of JSON files")
            if file_size_in_bytes > self.max_file_size_in_bytes:
                # Refuse to read or write a file bigger than self.max_file_size_in_bytes
                return True
        return False

    # Read the contents of self.file_path (expecting it to be a JSON-encoded list of dicts)
    def read(self) -> bool:
        # If the file doesn't exist don't bother reading it
        if not os.path.exists(self.file_path):
            print(f"Could not find, and therefore read from {self.file_path}.")
            return False

        # Don't read a file that's too big
        if self.file_size_is_too_big(os.path.getsize(self.file_path)):
            print(f"{self.file_path} is too big, refusing to read it.")
            return False

        # Open self.file_path for reading
        file_handle = None
        read_time = time.mktime(time.localtime())
        try:
            file_handle = open(self.file_path, "r")
        except OSError:
            print(f"{self.file_path} exists, but cannot be read.")
            return False

        # Read the contents of self.file_path as JSON, a list of dictionaries
        json_read = None
        try:
            json_read = json.load(file_handle)
            file_handle.close()
        except json.JSONDecodeError:
            print(f"{self.file_path} exists, but there was an error parsing it as JSON.")
            file_handle.close()
            return False

        # Log time of read
        self.last_sync = read_time

        # Parse contents of JSON read as a list of dictionaries
        self.list = []
        for dictionary in json_read:
            self.list_type_instance.from_dict(dictionary)
            self.list.append(self.list_type_instance.copy())

        # Return success
        return True

    # Save contents to self.file_path (should save a JSON-encoded list of dicts)
    def write(self) -> True:
        # Create a list of dicts to save to self.file_path
        list_of_dict = []
        for list_item in self.list:
            list_of_dict.append(list_item.to_dict())

        # Compute the JSON that will be dumped into the file, refuse if it's too big
        json_dump = json.dumps(list_of_dict)
        if self.file_size_is_too_big(len(json_dump)):
            print(f"The contents wishing to be written to {self.file_path} is too big, refusing to write it.")
            return False

        # Write to self.file_path, will overwrite old contents and make new file if one did not exist
        try:
            file_handle = open(self.file_path, "w")
            file_handle.write(json_dump)
            file_handle.close()
        except OSError:
            print(f"{self.file_path} could not be written to.")
            return False

        # Log time of write
        self.last_sync = time.mktime(time.localtime())

        # Return success
        return True

    # Return the index of the first element in self.list search_function for search_match return True
    def get_list_item_index(self, search_function, search_match) -> int:
        for i in range(len(self.list)):
            if search_function(self.list[i], search_match) == True:
                return i
        return -1
        
    # Return whether the contents of self.file_path are newer than that of memory, possible in multi-threaded situations
    def is_desynced(self) -> bool:
        try:
            return os.path.getmtime(self.file_path) > self.last_sync
        except OSError:
            return True

    # If the contents of memory are older than the contents of self.file_path, overwrite memory with the contents of self.file_path
    # TODO: In rare multi-threaded cases, because different threads cannot share file locks (to my knowledge), it is possible for
    #       one thread to write *while* another a reading, or multiple threads to write at the same time, or overwrite each other's changes
    #       because they both thought they were synced, and maybe they were! Lots of little finicky stuff. If only one thread writes it
    #       shouldn't be a problem. But if not... This is probably a common problem, maybe there's a library to help me? Make a proper database?
    def sync(self) -> bool:
        if self.is_desynced():
            return self.read()
        return False
