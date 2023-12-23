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
MAX_AUDIO_QUEUE_LENGTH = 20
MIN_VOLUME = .5
MAX_VOLUME = 2


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
    """
    def __init__(
        self,
        audio_queue_element_id: int = 0,
        author_user_id: int = 0,
        description: str = "",
        source_command: str = "",
        file_path: str = ""
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
            file_name: What to initialize self.file_name as
        """
        self.audio_queue_element_id = audio_queue_element_id
        self.author_user_id = author_user_id
        self.description = description
        self.source_command = source_command
        self.file_path = file_path

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
            + f"\nSource: `{self.source_command}`"

    def get_audio_source(
        self,
        play_volume: int = 1.0,
        play_offset: float = 0
    ) -> discord.FFmpegPCMAudio:
        """Create a Discord-friendly audio source for self.file_path.

        Create an FFMpegPCMAudio audio source for self.file_path, playing from
        offset seconds after the start, at (volume * 100)% volume.

        Args:
            self: This AudioQueueElement
            play_volume: At what volume to play this audio ((volume * 100)%).
            play_offset: How many seconds from the start of an audio to start
                playing the audio from.
        """
        # Check validity of arguments
        if play_volume < MIN_VOLUME or \
            play_volume > MAX_VOLUME or \
            play_offset < 0:
            return None

        # Assert file can be opened and read
        try:
            file_handle = open(self.file_path, "rb")
            file_handle.close()
        except OSError:
            print(f"WARNING: Audio source for {self.description} was " \
                + "requested but could not be produced because its file " \
                + f"location, {self.file_path}, could not be opened and read.")
            return None

        # Return audio source, if possible
        try:
            # vn = disable video
            # sn = disable subtitles
            # ss = at what timestamp to start audio from
            return discord.PCMVolumeTransformer(
                original = discord.FFmpegPCMAudio(
                    source = self.file_path,
                    options = f"-vn -sn -ss {seconds_to_timestamp(play_offset)}"
                ),
                volume = play_volume
            )
        except TypeError:
            print(f"WARNING: Audio source for {self.description} was " \
                + "requested but could not be produced because it was a " \
                + "non-audio source.")
        except ClientException:
            print(f"WARNING: Audio source for {self.description} was " \
                + "requested but could not be produced because it was opus " \
                + "encoded (using PCM, not opus player).")

        # An error occurred using the file, no audio source can be created
        return None

class AudioQueueList(commands.Cog):
    """Define a cog for managing a queue of audio to be played in voice chat.

    Define a Cog with a task to check for outstanding audio to play every
    second, while handling numerous edge cases, such as pausing, removing
    currently playing audio, and more.

    Attributes:
        voice_client: The voice client to play audio on
        queue: A list of AudioQueueElement to play
        latest_is_finished: Whether queue[0] has finished playing in its
            entirety and can be deleted.
        latest_offset: At what time offset into queue[0] to start playing from.
            Measured in seconds since the start of the audio file.
        latest_play_timestamp: At what time play() was last called on queue[0].
            Measured in seconds since the last epoch.
        paused_audio_was_deleted: Whether the queue[0] was paused and deleted,
            meaning it cannot be resumed on unpause.
        is_paused: Whether the audio queue is currently paused and has stopped
            playing audio.
        volume: The current volume to play audio at, for example 1.0 = 100%.
    """
    def __init__(self, voice_client: discord.VoiceClient):
        """Initialize this AudioQueueList.

        Set the members of this AudioQueueList to their defaults or passed in
        values.

        Args:
            self: This AudioQueueList
            voice_client: Waht to initialize self.voice_client as
        """
        self.voice_client = voice_client
        self.queue = []
        self.latest_is_finished = False
        self.latest_offset = 0.0
        self.latest_play_timestamp = 0.0
        self.paused_audio_was_deleted = False
        self.is_paused = False
        self.volume = 1.0
        self.play_next.start()

    def add(
        self,
        ctx: discord.ApplicationContext,
        description: str,
        file_path: str
    ) -> int:
        """Add a new AudioQueueElement to this AudioQueueList.

        If there is room in the audio queue, append new AudioQueueElement to the
        end of self.queue with the passed in parameters and a unique ID.

        Args:
            self: This AudioQueueList
            ctx: The ctx of the SlashCommand this function is being called from
            description: A human-readable description of the audio to play
            file_path: The path to the audio file to actually play

        Returns:
            The ID of the element once placed in queue. -1 if it was not placed.
        """
        # Do not allow addition of another audio source if queue is already full
        if len(self.queue) >= MAX_AUDIO_QUEUE_LENGTH:
            return -1

        # Generate unique audio_queue_element_id
        audio_queue_element_id = 0
        if len(self.queue) > 0:
            audio_queue_element_id = \
                (self.queue[-1].audio_queue_element_id + 1) % 1000

        # Add a new AudioQueueElement to this AudioQueueList with unique ID
        self.queue.append(
            AudioQueueElement(
                audio_queue_element_id = audio_queue_element_id,
                author_user_id = ctx.author.id,
                source_command = f"/{ctx.command.qualified_name}",
                description = description,
                file_path = file_path
            )
        )
        return audio_queue_element_id

    def remove(self, audio_queue_element_id: int) -> bool:
        """Remove an existing AudioQueueElement from this AudioQueueList.

        If an AudioQueueElement matching audio_queue_element_id exists within
        self.queue, remove it, and stop playing it if it is currently playing.

        Args:
            self: This AudioQueueList
            audio_queue_element_id: The ID of the AudioQueueElement to remove

        Returns:
            Whether the AudioQueueElement asking to be removed could be found
            and was removed.
        """
        # Find the index in queue of the AudioQueueSource with matching ID
        match_index = -1
        for i in range(len(self.queue)):
            if self.queue[i].audio_queue_element_id == audio_queue_element_id:
                match_index = i
                break

        # If there was no match index, there's nothing to delete, fail
        if match_index == -1:
            return False

        # If the match is the audio currently playing, need to stop it
        if match_index == 0:
            if self.is_paused is True:
                self.paused_audio_was_deleted = True
                self.queue.pop(match_index)
            else:
                self.voice_client.stop()
                self.latest_is_finished = True

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
        if self.voice_client.is_playing():
            self.voice_client.stop()
            self.latest_offset += time.time() - self.latest_play_timestamp

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

    # TODO: Enable this if supporting prioritized audio queues.
    #       I doubt ffmpeg or pycord can support sound mixing?
    #def interrupt(self, audio_source: discord.audio_source) -> None:
    #    """Interrupt the current audio queue to play a more important sound.
    #
    #    TODO.
    #    """
    #    # TODO: scenario with multiple interrupts? use differnt audio queue
    #    # for higher priority sounds?
    #    self.pause()
    #    self.voice_client.play(audio_source, after=self.unpause)

    # Every user in the call can already independently adjust the bot's volume
    # for themself, this feature may not be necessary, but the (non-functional)
    # code can stick around in case anyone requests it
    #def change_volume(self, volume: float) -> bool:
    #   """Change the volume of current and future audio in this AudioQueueList.
    #
    #    Change the volume, for yourself and others, of the audio in this audio
    #    queue. This is done by pausing, changing the volume member, and
    #    unpausing.
    #
    #    Attributes:
    #        self: This AudioQueueList
    #        volume: The volume to change self.volume to. A float, for example,
    #            1.45 = 145%.
    #
    #    Return:
    #        Whether the operation succeeded. It may not, for example, if the
    #        requested volume was unreasonable.
    #    """
    #    # Change volume going forward, deny if unreasonable
    #    if volume < .5 or volume > 2:
    #        return False
    #
    #    # If already paused, simply change volume, the change will be
    #    # automatically picked up whenever this AudioQueueList is unpaused
    #    if self.is_paused is True:
    #        self.volume = volume
    #    # Otherwise, pause, adjust volume, and unpause. The rest of the member
    #    # functions will pick up the slack of figuring out what to do.
    #    else:
    #        self.pause()
    #        self.volume = volume
    #        self.unpause()
    #
    #    return True

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
        # Remove finished audio from queue, reset intermediate state
        if self.latest_is_finished is True:
            self.queue.pop(0)
            self.latest_offset = 0
            self.latest_is_finished = False

        # Don't do anything else if:
        # - There are no audio elements queued
        # - We are already playing audio
        # - We are paused
        if len(self.queue) == 0 or \
            self.voice_client.is_playing() or \
            self.is_paused:
            return

        # Create audio_source
        # If an audio source cannot be created, it must be skipped
        audio_source = self.queue[0].get_audio_source(
            play_volume = self.volume,
            play_offset = self.latest_offset
        )
        if audio_source is None:
            self.queue.pop(0)
            return

        # Play audio_source
        self.latest_play_timestamp = time.time()
        init_play_after(self, "set_latest_is_finished", (True,))
        self.voice_client.play(audio_source, after=play_after)



# The after functions of play() not allowing parameters make me sad :(
# This code is horrible... Hiding it at the bottom.
# Anyways, get around not having params with globals.
global g_audio_queue_list
g_audio_list = None
global g_operation
g_operation = ""
global g_params
g_params = ()

def init_play_after(
    audio_queue_list: AudioQueueList,
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
        audio_queue_list: The audio queue list to do operation on
        operation: A string describing the operation on audio_queue_list you
            want to have happen after Discord.VoiceClient.play() finishes.
        params: A tuple of parameters for the operation, for example, if the
            operation is to set some value, what to set that value to.
    """
    global g_audio_queue_list
    global g_operation
    global g_params
    g_audio_queue_list = audio_queue_list
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

    global g_audio_queue_list
    global g_operation
    global g_params
    if g_operation == "set_is_paused":
        g_audio_queue_list.is_paused = g_params[0]
    elif g_operation == "set_latest_is_finished":
        # If the audio source was stopped because it is being paused, the
        # audio source is not finished
        if g_audio_queue_list.is_paused:
            g_audio_queue_list.latest_is_finished = False
        # Otherwise, set it to whatever the parameter is
        else:
            g_audio_queue_list.latest_is_finished = g_params[0]
