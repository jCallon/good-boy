"""TODO.

TODO.
"""

#==============================================================================#
# Import libraries                                                             #
#==============================================================================#

# Import operating system API for things like moving files
import os

# Import API for hashing text in a collision-resistant way
import hashlib

# Import API for handling ascii strings as binary lists
import binascii

#==============================================================================#
# Define underlying structure                                                  #
#==============================================================================#

CACHE_DIR = "cache"

class FileCacheElement():
    """TODO.

    TODO.

    Attributes:
        self: This FileCacheElement
        file_name: The name of file in a cache
        last_access_time: The last time the file matching self.file_name was
            accessed. This may not be the same as when it was made or last
            modified.
        size_in_bytes: The size, in bytes, of the file matching
            self.file_name
    """
    def __init__(
        self,
        directory: str,
        file_name: str
    ):
        """Initialize this FileCacheElement.

        Set the members of this FileCacheElement to the passed in values.

        Args:
            TODO
        """
        self.directory = directory
        self.file_name = file_name
        self.file_path = f"{self.directory}/{self.file_name}"
        stat = os.stat(self.file_path)
        self.last_access_time = stat.st_atime
        self.size_in_bytes = stat.st_size



class FileCacheList():
    """Define an API to monitor a directory and keep it within certain size.

    Define an API to monitor adding new files to a directory, that will
    ensure the directory never exceeds a certain size, by deleting the
    least recently accessed files to make room for new ones.

    Attributes:
        directory: The directory to monitor the files of
        max_bytes: The max size, in bytes, to allow the directory specified
            by self.directory get to
    """
    def __init__(
        self,
        directory: str,
        max_size_in_mega_bytes: int
    ):
        """Initialize this FileCacheList.

        Set the members of this FileCacheList to the passed in values.

        Args:
            self: This FileCacheList
            directory: What initialize self.directory as
            max_size_in_bytes: What initialize self.max_size_in_bytes as
        """
        self.directory = f"{CACHE_DIR}/{directory}"
        self.max_size_in_bytes = max_size_in_mega_bytes * 1000000
        # TODO: create directories if they don't exist

    def get_hashed_file_name(
        self,
        content_to_hash: tuple,
        file_extension: str
    ) -> str:
        """Generate a safe, unique file name for content_to_hash.

        Generate a unique file name for a file that may be distinguished by
        unsafe/unvalidated contents, such as user input.
        A great example of this is TTS, where we don't want to regenerate
        TTS audio we already have on disk, but we also don't want to save
        its file name as whatever arbitrary text they typed, such as an
        embedded bash command they typed to help someone else in call.
        Using a hash lets you always generate the same file name for the
        same content_to_hash, letting you find the file again later.
        Used: https://cryptobook.nakov.com/cryptographic-hash-functions.

        Args:
            self: This FileCacheList
            content_to_hash: A tuple of the information to hash to make the
                file name. In other words, what you want your file to be
                individually dinguishable by, such as text being said in it.
            file_extentension: The file type of the output file. For
                example: mp3, mp4, wav, txt.

        Returns:
            A file name, made from the concatenation of a hash of
            content_to_hash and file_extenstion.
        """
        # Create string which is just a concatenation of all the elements in
        # content_to_hash
        byte_array = ""
        for element_to_hash in content_to_hash:
            byte_array += str(element_to_hash)

        # Encode the concatenation as a bytearray, then hash it
        byte_array = byte_array.encode()
        byte_array = binascii.hexlify(hashlib.sha3_256(byte_array).digest())

        # Return the result of the hash + file_extension
        return f"{byte_array}.{file_extension}"

    def get_file_path(self, file_name: str) -> str:
        """Get the file path of file_name if it were in self.directory.

        Generate the relative file path of where file_name would be stored
        if it were stored within the directory sepcified by self.directory.

        Args:
            self: This FileCacheList
            file_name: The name of the file you wish to get the path of

        Returns:
            A concatenation of self.directory and file_name.
        """
        return f"{self.directory}/{file_name}"

    def file_exists(self, file_name: str) -> bool:
        """Check whether file_name exists within self.directory.

        Check whether the file specified by file_name already exists, is
        openable, and is readable in the directory specified by
        self.directory.

        Args:
            self: This FileCacheList
            file_name: The name of the file you wish to know whether exists

        Returns:
            Whether self.directory/file_name exists, is openable, and is
            readable.
        """
        can_open_and_read = True
        try:
            file_handle = open(self.get_file_path(file_name), "rb")
            file_handle.close()
        except OSError:
            can_open_and_read = False
        return can_open_and_read

    def add(self, file_name: str) -> bool:
        """Try adding a new file to the directory at self.directory.

        Try to add the file specified by file_name to the directory at
        self.directory, making sure not to go over self.max_size_in_bytes.
        Make room for the new file, if needed, by deleting the least
        recently accessed files in self.directory first, until there is
        space for the file, and sum of the sizes of all the files within
        self.directory is within self.max_size_in_bytes.

        Args:
            self: This FileCacheList
            file_name: The name of the file you wish to add to the directory
                specified by self.directory

        Returns:
            Whether the operation was successful. It may not be, for 
            example, if deleting every file in the directory specified by
            self.directory would not make enough room for the new file.
        """
        # Assumes file is already downloaded in cache/, but no deeper

        # Execute all code calling the os library within the safety of a try
        # Assuming you gave a file_name that exists, and you created your
        # cache_directory correctly, these *should* never throw an error
        try:
            # Get information on the new file
            new_file = FileCacheElement(CACHE_DIR, file_name)

            # If this file is bigger than the directory is allowed to be,
            # it'll be impossible to add this file while staying within size
            # constraints
            if new_file.size_in_bytes > self.max_size_in_bytes:
                os.path.remove(new_file.file_path)
                return False

            # If adding this file would not put us over 
            # self.max_size_in_bytes, can just move it into self.directory,
            # no fuss
            if os.path.getsize(self.directory) + new_file.size_in_bytes <= \
                self.max_size_in_bytes:
                os.rename(new_file.file_path, self.get_file_path(file_name))
                return True

            # This file is safe to add to self.directory and requires other
            # files within self.directory to be deleted to have it fit
            # within self.max_size_in_bytes...
            # Get all file names, access times, and sizes.
            files_in_directory = []
            for file_name in os.listdir(self.directory):
                files_in_directory.append(FileCacheElement(file_name))

            # Sort file_cache_element_sorted_list access time,
            # [0] == least recently accessed
            files_in_directory = sorted(
                files_in_directory,
                key=lambda file_info: file_info.last_access_time
            )

            # Remove least recently accessed files until we have enough
            # space for the new file
            while self.max_size_in_bytes > \
                os.path.getsize(self.directory) + new_file_size_in_bytes:
                os.path.remove(
                    self.get_file_path(files_in_directory[0].file_name)
                )
                files_in_directory.pop(0)

            # Move the file from general cache into this cache, now that
            # there's room
            os.rename(new_file.file_path, self.get_file_path(file_name))

        except OSError as error:
            print(error)
            return False

        return True
