"""Define API for managing adding files to a directory.

Define an API for adding new files to a directory with space limitations.
Reduces bloat on the bot owner's computer, while, if used right, also reducing
overhead from uneccessary redownloads.
"""

#==============================================================================#
# Import libraries                                                             #
#==============================================================================#

# Import API for spawning subprocesses for running command-line prompts
import subprocess

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
    """Define an instance of useful information on a file.

    Define an instance of information on a file useful for FileCacheList to
    manage a directory.

    Attributes:
        directory: The directory containing the file matching self.file_name
        file_name: The name of the file to get/store information for
        last_access_time: The last time the file matching self.file_name was
            accessed. This may not be the same as when it was made or last
            modified.
        size_in_bytes: The size, in bytes, of the file matching self.file_name
    """
    def __init__(
        self,
        directory: str,
        file_name: str
    ):
        """Initialize this FileCacheElement.

        Set self.directory and self.file_name to the passed in values, then
        derive this FileCacheElement's other members from self.directory and
        self.file_name through concatenation and OS calls.

        Args:
            self: This FileCacheElement
            directory: The directory of the file to get information on
            file_name: The name of the file to get information on
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
        max_bytes: int
    ):
        """Initialize this FileCacheList.

        Set the members of this FileCacheList based on passed in values.

        Args:
            self: This FileCacheList
            directory: What initialize self.directory as
            max_size_in_bytes: What initialize self.max_size_in_bytes as
        """
        self.directory = f"{CACHE_DIR}/{directory}"
        self.max_bytes = max_bytes
        # TODO: Create directories if they don't exist?

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
        embedded bash command someone typed to help someone else in-call.
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
        # Create a string which is just a concatenation of all the elements in
        # content_to_hash
        byte_array = ""
        for element_to_hash in content_to_hash:
            byte_array += str(element_to_hash)

        # Encode the concatenation as a bytearray, then hash it
        byte_array = byte_array.encode()
        byte_array = binascii.hexlify(hashlib.sha3_256(byte_array).digest())

        # Return the result, a concatenation of the hash and file_extension
        # (printing byte_array directly prints b'...', remove all but ...)"
        byte_array_as_str = f"{byte_array}"
        return f"{byte_array_as_str[2:-1]}.{file_extension}"

    def get_file_path(self, file_name: str) -> str:
        """Get the file path of file_name if it were in self.directory.

        Generate the relative file path for where file_name would be stored
        if it were stored within the directory specified by self.directory.

        Args:
            self: This FileCacheList
            file_name: The name of the file you wish to get the path of

        Returns:
            A concatenation of self.directory and file_name.
        """
        return f"{self.directory}/{file_name}"

    def file_exists(self, file_name: str) -> bool:
        """Check whether file_name exists within self.directory.

        Check whether the file specified by file_name already exists in
        self.directory.

        Args:
            self: This FileCacheList
            file_name: The name of the file you wish to know whether exists

        Returns:
            Whether self.directory/file_name exists.
        """
        return os.path.isfile(self.get_file_path(file_name))

    def add(self, file_name: str, normalize_audio : bool) -> bool:
        """Move a file downloaded to cache to self.directory.

        After you've downloaded a file in CACHE_DIR, use this function to try
        to add it to the directory at self.directory.
        Update me.
        If the file matching file_name is larger than self.max_bytes, don't
        allow the file in self.directory and delete it.
        Otherwise, remove every file in self.directory, starting from the least
        recently accessed, until adding the file matching file_name to
        self.directory would not make the directory exceed self.max_bytes, then,
        move the file to self.directory.

        Args:
            self: This FileCacheList
            file_name: The name of the file you wish to move to the directory
                specified by self.directory
            normalize_audio: If file_name is an audio file, whether to use
                ffmpeg-normalize to normalize its audio. If you're not familiar,
                for this purpose, normalizing audio is making it a near-constant
                volume, so it has a smoother listening experience and doesn't
                surprise anyone with sudden loud bursts.

        Returns:
            Whether the operation was successful. It may not be, for
            example, if deleting every file in the directory specified by
            self.directory would not make enough room for the new file.
        """
        # Assumes file is already downloaded in CACHE_DIR, but no deeper

        # Execute all code calling the os library within the safety of a try
        # Assuming you gave a file_name that exists, and you created your
        # cache_directory correctly, these *should* never throw an error
        try:
            # Assert the file name cannot be harmful (is all non-special ASCII)
            #safe_file_name = ""
            #for character in file_name:
            #    if ord("0") <= ord(character) <= ord("9") or \
            #        ord("A") <= ord(character) <= ord("Z") or \
            #        ord("a") <= ord(character) <= ord("z") or \
            #        character == ".":
            #        safe_file_name += character
            #    else:
            #        safe_file_name += "_"
            #file_name = safe_file_name

            # Normalize the audio via ffmpeg-normalize
            # See: https://github.com/slhck/ffmpeg-normalize/wiki/examples
            if normalize_audio is True:
                # Create a new normalized version of the audio
                completed_process = subprocess.run([
                    # Command name
                    "ffmpeg-normalize",
                    # Input file
                    f"{CACHE_DIR}/{file_name}",
                    # Output file
                    "-c:a",
                    "libmp3lame",
                    "-o",
                    f"{CACHE_DIR}/normalized_{file_name}",
                ])
                if completed_process.returncode != 0:
                    raise OSError()

                # Overwrite the non-normalized version of the file
                os.remove(f"{CACHE_DIR}/{file_name}")
                os.rename(
                    src = f"{CACHE_DIR}/normalized_{file_name}",
                    dst = f"{CACHE_DIR}/{file_name}",
                )

            # Get information on the new file
            new_file = FileCacheElement(CACHE_DIR, file_name)

            # If this file is bigger than the directory is allowed to be,
            # it'll be impossible to add this file while staying within size
            # constraints, remove it entirely
            if new_file.size_in_bytes > self.max_bytes:
                os.path.remove(new_file.file_path)
                return False

            # If adding this file would not put self.directory over
            # self.max_bytes, can just move it into self.directory,
            # no fuss
            if os.path.getsize(self.directory) + new_file.size_in_bytes <= \
                self.max_bytes:
                os.rename(new_file.file_path, self.get_file_path(file_name))
                return True

            # This file is safe to add to self.directory and requires other
            # files within self.directory to be deleted to have it fit
            # within self.max_bytes...

            # Get each file name, access time, etc. in self.directory
            files_in_dir = []
            for file_name_in_dir in os.listdir(self.directory):
                files_in_dir.append(
                    FileCacheElement(
                        directory = self.directory,
                        file_name = file_name_in_dir
                    )
                )

            # Sort file_cache_element_sorted_list by access time,
            # [0] == least recently accessed
            files_in_dir = sorted(
                files_in_dir,
                key=lambda file_info: file_info.last_access_time
            )

            # Remove the least recently accessed file until we have enough
            # space for the new file
            while self.max_bytes > \
                os.path.getsize(self.directory) + new_file.size_in_bytes:
                os.path.remove(self.get_file_path(files_in_dir[0].file_name))
                files_in_dir.pop(0)

            # Move the file from general cache into this cache, now that
            # there's room
            os.rename(new_file.file_path, self.get_file_path(file_name))

        except OSError as error:
            print(error)
            return False

        return True
