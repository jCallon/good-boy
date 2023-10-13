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
    # Convert dict into member variables
    def to_dict(self) -> dict:
        raise NotImplementedError

    # Convert member variables into dict
    def from_dict(self, dictionary: dict) -> None:
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

    # Return whether the length of data wishing to be stored is allowable, give a warning if it's close
    def file_size_is_too_big(self, new_file_size_in_bytes: int) -> bool:
        # Check if the file size is at or near threshold
        if new_file_size_in_bytes * 0.75 > self.max_file_size_in_bytes:
            # Give the bot owner a warning with possible solutions
            print(f"{self.file_path} is full or near full, at {new_file_size_in_bytes} bytes of {self.max_file_size_in_bytes} max bytes.")
            print(f"Please pause or kill the bot and do one of these 3 options:")
            print(f" 1. Make a backup and manually remove uneeded info")
            print(f" 2. Increase the max file size")
            print(f" 3. Make hyper-optimized versions of to_dict and from_dict methods")
            if file_size_in_bytes > self.max_file_size_in_bytes:
                # Refuse to read or write a file bigger than self.max_file_size_in_bytes
                return True
        return False

    # Read the contents of self.file_name (should be a list of dicts)
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
        self.last_sync = time.mktime(time.localtime())

        # Parse contents of JSON read as a list of dictionaries
        self.list = []
        for dictionary in json_read:
            self.list_type_instance.from_dict(dictionary)
            self.list.append(self.list_type_instance.copy())

        # Return success
        return True

    # Save contents to self.file_path (should save a list of dicts)
    # TODO: make sure write directory exists
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
        file_handle = open(self.file_path, "w")
        file_handle.write(json_dump)
        file_handle.close()

        # Log time of write
        self.last_sync = time.mktime(time.localtime())

        # Return success
        return True

    # Return the index of the first self.list item that makes search_function return True
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
    # TODO: In (rare, but less rare the bigger the files get) multi-threaded cases, it is possible
    #       between a self.sync() and self.write() for the contents of self.file_path to get overwritten to by a different thread.
    #       That means in small time windows, different threads can overwrite each other's changes to the same file.
    #       This is probably a common problem, maybe there's a library to help me?
    def sync(self) -> bool:
        if self.is_desynced():
            return self.read()
        return False
