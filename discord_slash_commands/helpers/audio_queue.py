"""Functions for 'queueing' audio to play in voice chat.

This file defines some helpers for playing audio consecutively in voice chat.
The current implementation in this file is very ugly and basic, and open to
improvements.
"""

#==============================================================================#
# Import libraries                                                             #
#==============================================================================#

# Import API for doing basic math conversion
import math

# Import API for keeping track of time
import time

# Import Discord Python API
import discord

# Import Discord extended APIs to create timed tasks
from discord.ext import commands, tasks

#==============================================================================#
# Define underlying structure                                                  #
#==============================================================================#

# Define some constants to avoid copy/paste
MIN_VOLUME = .5
MAX_VOLUME = 2
LOW_PRIORITY = 0
MEDIUM_PRIORITY = 1
HIGH_PRIORITY = 2



def timestamp_to_seconds(timestamp : str) -> float:
    """Derive seconds from HH:MM:SS-like timestamp.

    Return the total number of seconds indicated by a HH:MM:SS-like timestamp.
    Ex. 0:52.22 = 52.22 seconds
    3:21 = 3 minutes and 21 seconds = 201 seconds
    50:24:46 = 50 hours, 24 minutes, and 46 seconds = 181486 seconds

    Args:
        timestamp: The HH:MM:SS-like timestamp to parse.

    Returns:
        The total number of seconds represented by timestamp.

    Raises:
        ValueError: Some part of timestamp was an unsupported format and could
            not be read.
    """
    timestamp = timestamp.split(":")
    hours = 0
    minutes = 0
    seconds = 0
    if len(timestamp) == 3:
        hours = int(timestamp[0])
        minutes = int(timestamp[1])
        seconds = float(timestamp[2])
    else:
        minutes = int(timestamp[0])
        seconds = float(timestamp[1])
    return (hours * 60 * 60) + (minutes * 60) + seconds



def seconds_to_timestamp(total_seconds : float) -> str:
    """Format seconds into HH:MM:SS-like timestamp.

    Return a HH:MM:SS-like timestamp given a total number of seconds.
    Ex. 52.22 seconds = 0:52.22
    201 seconds = 3 minutes and 21 seconds = 3:21
    181486 seconds = 50 hours, 24 minutes, and 46 seconds = 50:24:46

    Args:
        total_seconds: The number of seconds to represent in the returned
            timestamp.

    Returns:
        A HH:MM:SS-like timestamp for total_seconds.
    """
    hours = 0
    while total_seconds > (60 * 60):
        hours += 1
        total_seconds -= (60 * 60)
    minutes = 0
    while total_seconds > 60:
        minutes += 1
        total_seconds -= 60
    seconds = float(total_seconds)

    # NOTE: The timestamp outputted will only have 2 decimal places of accuracy.
    # This is for ffmpeg compatibility (it does not support, say, 10 places)
    timestamp = ""
    timestamp += f"{hours}:" if hours > 0 else ""
    timestamp += f"{minutes}".zfill(2) if hours > 0 else f"{minutes}"
    timestamp += ":"
    timestamp += f"{math.floor(seconds)}".zfill(2)
    timestamp += "." if seconds % 1 != 0 else ""
    timestamp += f"{math.floor((seconds % 1) * 100)}".zfill(2) \
        if seconds % 1 != 0 else ""
    return timestamp



class AudioQueueElement():
    """Define an instance of information held on audio queued for playing.

    Define what information we should keep track of for each audio source in the
    audio queue. Most fields are for user-friendliness, so users can identify
    each audio file in the queue in a way meaningful to them. For example,
    one of my admins may be interested in seeing who is queuing annoying stuff.
    And, the names of the audio files are often not enough for a user to go on
    to identify what audio will be played from the file. File names are often
    hashed or mangled to ASCII to be safe for the bot-owner's computer.

    Attributes:
        audio_queue_element_id: An unique integer identifier for distinguishing
            this AudioQueueElement from others, independent of position in
            AudioQueueList.queue, which may be in constant flux. Used by users
            trying to modify the audio queue.
        author_user_id: The ID of the user who added this AudioQueueElement to
            the AudioQueueList. For users viewing the audio queue.
        source_command: How this AudioQueueElement was added to
            AudioQueueList.queue. For users viewing the audio queue.
        description: A human-readable description of the content of the audio to
            be played. For users viewing the audio queue. File names are often
            hashed and not helpful to a user.
        file_path: The path to the file to actually play once it's this
            AudioQueueElement's turn to play in voice chat.
        priority: The priority level of this audio, for example, 0 =
            LOW_PRIORITY, and 2 = HIGH_PRIORITY.
        time_started_play: When this audio file last had play() called on it,
            measured in seconds since the last epoch.
        time_played: The number of seconds of this audio played in voice chat.
            Used to know from what timestamp to resume paused audio from.
        is_finished: Whether this audio source has played until its end.
    """
    def __init__(
        self,
        audio_queue_element_id: int = 0,
        author_user_id: int = 0,
        description: str = "",
        source_command: str = "",
        file_path: str = "",
        priority: int = 0,
    ):
        """Initialize this AudioQueueElement.

        Set the members of this AudioQueueList to the passed in values.

        Args:
            self: This AudioQueueElement
            audio_queue_element_id: What to initialize
                self.audio_queue_element_id as
            author_user_id: What to initialize self.author_user_id as
            description: What to initialize self.description as
            source_command: What to initialize self.source_command as
            file_path: What to initialize self.file_name as
            priority: What to initialize self.priority as
        """
        self.audio_queue_element_id = audio_queue_element_id
        self.author_user_id = author_user_id
        self.description = description
        self.source_command = source_command
        self.file_path = file_path
        self.priority = priority
        self.time_started_play = 0.00
        self.time_played = 0.00
        self.is_finished = False
        self.is_paused = False

    def to_str(self) -> None:
        """Convert this AudioQueueElement to a string.

        Make a string including each member of this AudioQueueElement, formatted
        in an easy, human-readable way for Discord.

        Args:
            self: This AudioQueueElement
        """
        return f"\nID: `{self.audio_queue_element_id}`" \
            + f"\nAuthor: <@{self.author_user_id}>" \
            + f"\nDescription: `{self.description}`" \
            + f"\nSource: `{self.source_command}`" \
            + f"\nPriority: `{self.priority}`"

    def play(
        self,
        voice_client: discord.VoiceClient,
        volume: int = 1.0
    ) -> bool:
        """Play this AudioQueueElement in voice_client.

        Play self.file_path on voice_client at a (volume * 100)% volume.

        Args:
            self: This AudioQueueElement
            voice_client: What voice client to play self.file_path on
            volume: At what volume to play self.file_path at.
                1.0 = 100% = normal volume, 2.0 = 200% = high volume, etc.

        Returns:
            Whether self.file_path could be successfully played in voice_client.
        """
        # Check validity of arguments
        if volume < MIN_VOLUME or volume > MAX_VOLUME:
            return False

        # Assert file can be opened and read
        try:
            file_handle = open(self.file_path, "rb")
            file_handle.close()
        except OSError:
            print(f"WARNING: Audio source for {self.description} was " \
                + "requested but could not be produced because its file " \
                + f"location, {self.file_path}, could not be opened and read.")
            return False

        # Make audio source, if possible
        audio_source = None
        try:
            # vn = disable video
            # sn = disable subtitles
            # ss = at what timestamp to start audio from
            audio_source = discord.PCMVolumeTransformer(
                original = discord.FFmpegPCMAudio(
                    source = self.file_path,
                    options = "-vn -sn -ss " \
                        + f"{seconds_to_timestamp(self.time_played)}"
                ),
                volume = volume
            )
        except TypeError:
            print(f"WARNING: Audio source for {self.description} was " \
                + "requested but could not be produced because it was a " \
                + "non-audio source.")
            return False
        except ClientException:
            print(f"WARNING: Audio source for {self.description} was " \
                + "requested but could not be produced because it was opus " \
                + "encoded (using PCM, not opus player).")
            return False

        # Play audio source
        try:
            init_play_after(self, "set_is_finished", (True,))
            voice_client.play(audio_source, after=play_after)
        except ClientException:
            print("WARNING: Could not play audio source for " \
                + f"{self.description} because already the voice connection " \
                + "was already playing audio or isn't connected.")
            return False
        except TypeError:
            print("WARNING: Could not play audio source for " \
                + f"{self.description} because the audio source or after " \
                + "is not callable. ")
            return False
        except OpusNotLoaded:
            print("WARNING: Could not play audio source for " \
                + f"{self.description} because the audio source is Opus " \
                + "encoded and opus is not loaded.")
            return False
            
        self.time_started_play = time.time()
        self.is_paused = False
        return True

    def pause(self, voice_client: discord.VoiceClient) -> None:
        """Pause playing this AudioQueueElement.

        Stop playing this AudioQueueElement in voice chat, and remember current
        progress to resume from later.

        Args:
            self: This AudioQueueElement
            voice_client: What voice client to stop playing on
        """
        self.is_paused = True
        if voice_client.is_playing():
            voice_client.stop()
            self.time_played = time.time() - self.time_started_play




class AudioQueueList(commands.Cog):
    """Define a cog for managing a queue of audio to be played in voice chat.

    Define a Cog with a task to check for outstanding audio to play every
    second, while handling numerous edge cases, such as pausing, removing
    currently playing audio, and more.

    Attributes:
        voice_client: The discord.VoiceClient to play audio on.
        num_priority_levels: The number of levels of priority an audio source
            can have. Higher number = higher priority. Low priority audio is
            always paused and delayed for as long as it takes to play higher
            priority audio.
        queue_list: A list of num_priority_levels lists of AudioQueueElement.
            queue_list[0] = a list of what audio is queued with a priority of 0.
            queue_list[0][0] = the AudioQueueElement that's been in priority 0
            queue the longest, in other words, the audio source that should be
            played soonest (assmuming higher priority audio isn't
            queued/playing).
        max_queue_length: The maximum number of AudioQueueElement to allow
            across all of queue_list.
        latest_audio: The audio currently playing or paused in voice chat.
        is_paused: Whether playing of all audio queues has been paused.
        volume: The current volume to play audio at, for example 1.0 = 100%.
    """
    def __init__(self, voice_client: discord.VoiceClient):
        """Initialize this AudioQueueList.

        Set the members of this AudioQueueList to their defaults or passed in
        values.

        Args:
            self: This AudioQueueList
            voice_client: What to initialize self.voice_client as
        """
        self.voice_client = voice_client
        self.num_priority_levels = 3
        self.queue_list = []
        for i in range(self.num_priority_levels):
            self.queue_list.append([])
        self.max_queue_length = 20
        self.latest_audio = None
        self.is_paused = False
        self.volume = 1.0
        self.play_next.start()

    def get_num_audio_files_queued(self) -> int:
        """Get the combined length of all this AudioQueueList's audio queues.

        Get the number of AudioQueueElements in self.queue_list across all
        priority levels.

        Args:
            self: This AudioQueueElement

        Returns:
            The number of AudioQueueElement self.queue_list stores.
        """
        num_audio_files_queued = 0
        for queue in self.queue_list:
            num_audio_files_queued += len(queue)
        return num_audio_files_queued

    def add(
        self,
        ctx: discord.ApplicationContext,
        description: str,
        file_path: str,
        priority: int 
    ) -> int:
        """Add a new AudioQueueElement to this AudioQueueList.

        If there is room in the audio queue, append new AudioQueueElement to the
        end of self.queue with the passed in parameters and a unique ID.

        Args:
            self: This AudioQueueList
            ctx: The ctx of the SlashCommand this function is being called from
            description: A human-readable description of the audio to play
            file_path: The path to the audio file to actually play
            priority: The priority level of the audio to play. Please use the
                a constant at the top of this file for better readability
                (LOW_PRIORITY, MEDIUM_PRIORITY, etc.).

        Returns:
            The ID of the element once placed in queue. -1 if it was not placed.
        """
        # Do not allow addition of another audio source if queue is already full
        if self.get_num_audio_files_queued() >= self.max_queue_length:
            return -1

        # The queue to modify depends on the priority
        if priority >= self.num_priority_levels:
            return -1
        queue = self.queue_list[priority]

        # Generate unique audio_queue_element_id for audio_queue
        audio_queue_element_id = 0
        if len(queue) > 0:
            audio_queue_element_id = \
                (queue[-1].audio_queue_element_id + 1) % 1000

        # Add a new AudioQueueElement to this AudioQueueList with unique ID
        queue.append(
            AudioQueueElement(
                audio_queue_element_id = audio_queue_element_id,
                author_user_id = ctx.author.id,
                source_command = f"/{ctx.command.qualified_name}",
                description = description,
                file_path = file_path,
                priority = priority
            )
        )
        return audio_queue_element_id

    def remove(
        self,
        audio_queue_element_id: int,
        priority: int
    ) -> bool:
        """Remove an existing AudioQueueElement from this AudioQueueList.

        If an AudioQueueElement matching audio_queue_element_id exists within
        self.queue, remove it, and stop playing it if it is currently playing.

        Args:
            self: This AudioQueueList
            audio_queue_element_id: The ID of the AudioQueueElement to remove
            priority: The priority level of the audio to remove.

        Returns:
            Whether the AudioQueueElement asking to be removed could be found
            and was removed.
        """
        # The queue to modify depends on the priority
        if priority >= self.num_priority_levels:
            return -1
        queue = self.queue_list[priority]

        # Find the index in queue of the AudioQueueSource with matching ID
        match_index = -1
        for i in range(len(queue)):
            if queue[i].audio_queue_element_id == audio_queue_element_id:
                match_index = i
                break

        # If there was no match, there's nothing to delete, fail
        if match_index == -1:
            return False

        # Remove the audio from queue_list, stop it if it's currently playing
        if self.latest_audio == queue[match_index]:
            self.latest_audio.pause()
        queue.pop(match_index)

        # Return success
        return True

    def pause(self) -> None:
        """Stop playing audio until unpaused.

        Pause the audio queue, stopping its current audio and saving its
        progress, so it can be resumed from the same point at a later time.

        Args:
            self: This AudioSourceList
        """
        # If already paused don't do anything
        if self.is_paused is True:
            return

        # Set is_paused to True so play_next() pauses playing audio
        self.is_paused = True

        # If audio is currently playing, stop it, and remember its progress
        self.latest_playing.pause()

    def unpause(self) -> None:
        """Keep playing audio until paused.

        Unpause the audio queue, restoring its progress, if possible, from when
        it was paused. This may not be possible, if, for example, the audio file
        has been deleted from queue or disk while the bot was paused.

        Args:
            self: This AudioSourceList
        """
        # If already unpaused don't do anything
        if self.is_paused is False:
            return

        # Resume queue, play_next() should automatically pick up progress
        self.is_paused = False

    # NOTE: There's probably a more efficient way to do this, such as with
    # events and listeners
    # TODO: Use discord.BaseActivity to display statuses of the bot, such as
    # paused, or the url and progress of what it's playing
    @tasks.loop(seconds=1.0)
    async def play_next(self) -> None:
        """Play the next AudioQueueElement in queue.

        Play queue[0] in voice chat unless paused, already playing something,
        or there is nothing to play.

        Args:
            self: This AudioQueueList
        """
        # Remove finished audio from each queue
        for queue in self.queue_list:
            if len(queue) > 0 and queue[0].is_finished:
                queue.pop(0)

        # Don't do anything else if there is nothing to play or we are paused
        if self.get_num_audio_files_queued() == 0 or self.is_paused is True:
            return

        # Get the highest priority audio
        highest_priority_audio = self.latest_audio
        for priority in reversed(range(self.num_priority_levels)):
            if len(self.queue_list[priority]) > 0:
                highest_priority_audio = self.queue_list[priority][0]
                break

        # If audio is currently playing...
        if self.voice_client.is_playing():
            # If it's the highest priority audio, let it keep going
            if self.latest_audio == highest_priority_audio:
                return
            # Otherwise, we need to pause the audio currently being played
            else:
                if self.voice_client.is_playing():
                    self.latest_audio.pause(self.voice_client)

        # Play highest priority audio, if possible, otherwise remove it
        self.latest_audio = highest_priority_audio
        if self.latest_audio.play(self.voice_client, self.volume) is False:
            self.queue.pop(0)
            return



# The after functions of play() not allowing parameters make me sad :(
# This code is horrible... Hiding it at the bottom.
# Anyways, get around not having params with globals.
global g_audio_queue_element
g_audio_list = None
global g_operation
g_operation = ""
global g_params
g_params = ()

def init_play_after(
    audio_queue_element: AudioQueueElement,
    operation: str,
    params: tuple
) -> None:
    """Set parameters for Discord.VoiceClient.play()'s after function.

    Initialize some global variables that will be used by play_after(), a
    function meant to be used as the after parameter of
    Discord.VoiceClient.play(). play()'s after function does not allow for any
    other parameter than error, so this is the only way I could think of to get
    around that, and do something very specific after an audio source has
    exhausted itself.

    Args:
        audio_queue_element: The AudioQueueElement to do operation on
        operation: A string describing the operation on audio_queue_list you
            want to have happen after Discord.VoiceClient.play() finishes.
        params: A tuple of parameters for the operation, for example, if the
            operation is to set some value, what to set that value to.
    """
    global g_audio_queue_element
    global g_operation
    global g_params
    g_audio_queue_element = audio_queue_element
    g_operation = operation
    g_params = params

def play_after(error) -> None:
    """A fine-grained after function for Discord.VoiceClient.play().

    A function meant to be be used as the after parameter of
    Discord.VoiceClient.play(). What it does is determined by the previous
    init_play_after() call, to allow very fine-grain control of what happens
    after an audio source is exhausted or stop()ed.

    Args:
        error: Any error that occurred during playing play()'s audio source.
    """
    if error is not None:
        print(error)

    global g_audio_queue_element
    global g_operation
    global g_params
    if g_operation == "set_is_finished":
        # If the audio source was stopped because it is being paused, the
        # audio source is not finished
        if g_audio_queue_element.is_paused:
            g_audio_queue_element.is_finished = False
        # Otherwise, set it to whatever the parameter is
        else:
            g_audio_queue_element.is_finished = g_params[0]
