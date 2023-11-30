"""PyCord.SlashCommand for playing YotTube audio in voice chat.

This file defines slash commands for letting a member play audio from YouTube
videos in their current connected voice chat.
"""

#==============================================================================#
# Import public libraries                                                      #
#==============================================================================#

# TODO: comment
import youtube_dl

# Import Discord Python API
import discord

# Import functions for asserting bot state
import discord_slash_commands.helpers.application_context_checks as ctx_check

# Import helper for queueing audio in voice chat
from discord_slash_commands.helpers import audio_queue

# Import helper for queueing audio in voice chat
from discord_slash_commands.helpers import file_cache

#==============================================================================#
# Define underlying structure                                                  #
#==============================================================================#

# Create instance of file cache for Youtube audio files
youtube_file_cache = file_cache.FileCacheList(
    directory = "youtube",
    max_size_in_mega_bytes = 100
)



# Create youtube slash command group
youtube_slash_command_group = discord.SlashCommandGroup(
    checks = [ctx_check.assert_author_is_allowed_to_call_command],
    #default_member_permissions = default,
    description = "Youtube commands",
    #description_localizations = default,
    #guild_ids = default,
    guild_only = True,
    name = "youtube",
    #name_localizations = default,
    #nsfw = default,
    #parent = default
)



# From example: https://github.com/ytdl-org/youtube-dl#embedding-youtube-dl
class YoutubeDlLogger(object):
    """Define a logger for youtube-dl.

    Define a class to serve as a logger for youtube-dl, which will capture all
    debug messages, warnings, and errors output by youtube-dl.

    Attributes:
        message_list: A list of tuples of messages that occured while running
            youtube-dl. tuple[0] = message source, tuple[1] = message content.
            Stored in the order the were outputted by youtube-dl.
        had_error: Whether an error occured during youtube-dl.
    """
    def __init__(self):
        """Initialize this YoutubeDlLogger.

        Set the members of this YoutubeDlLogger to their defaults.

        Args:
            self: This YoutubeDlLogger
        """
        self.message_list = []
        self.had_error = False

    def get_messages(self, message_source: str) -> list:
        """Get all messages output by youtube-dl from message_source.

        Get all messages from message_source outputted by youtube-dl from the
        last time this YoutubeDlLogger was used as the logger of youtube-dl.

        Args:
            self: This YoutubeDlLogger
            message_source: The source of the youtube-dl message. The current
                options are "debug", "warning", and "error".

        Returns:
            A list containing each message from message_source in
            self.message_list.
        """
        matches = []
        for message in self.message_list:
            if message[0] == message_source:
                matches.append(message[1])
        return matches

    def debug(self, message) -> None:
        """Handler for when youtube-dl throws a debug message.

        Log a debug message thrown by youtube-dl.

        Args:
            self: This YoutubeDlLogger
            message: The message thrown by youtube-dl
        """
        self.message_list.append(("debug", message))
        pass

    def warning(self, message) -> None:
        """Handler for when youtube-dl throws a warning message.

        Log a warning message thrown by youtube-dl.

        Args:
            self: This YoutubeDlLogger
            message: The message thrown by youtube-dl
        """
        self.message_list.append(("warning", message))
        pass

    def error(self, message) -> None:
        """Handler for when youtube-dl throws an error message.

        Log an error message thrown by youtube-dl. Log that an error occured.

        Args:
            self: This YoutubeDlLogger
            message: The message thrown by youtube-dl
        """
        self.message_list.append(("error", message))
        self.had_error = True
        pass

    def print_log(self) -> None:
        """Print all messages thrown by youtube-dl.

        Print the source and contents of each message thrown by youtube-dl the
        last time this YoutubeDlLogger was used as a logger for youtube-dl, in
        the same order they came in.

        Args:
            self: This YoutubeDlLogger
        """
        for message in self.message_list:
            print(f"{message[0]}: {message[1]}")



class YoutubeFile():
    """Define info to hold on a YouTube video when trying to download it.

    Define an instance holding useful information on a single Youtube video file
    when trying to download it via youtube-dl.

    Attributes:
        url: The url of the YouTube video to use youtube-dl to download
        video_file_name: If the url was valid, the name of the video file
            pointed to by it, stripped of non-ascii chracters.
        audio_file_name: video_file_name, but with an mp3 file type instead
        length_in_seconds: An integer containing the length of the YouTube video
            pointed to by url in seconds.
        logger: A logger instance to hold exactly how the youtube-dl transaction
            to get video_file_name went
    """
    def __init__(self, url: str):
        """Initialize this YoutubeFile.

        Initialize the members of this YoutubeFile to their defaults or passed
        in values, then run a youtube-dl query to get what the values of
        self.video_file_name and self.audio_file_name should be. Keep a log of
        the transaction in self.logger.

        Args:
            self: This YoutubeFile
            url: What to initialize self.url as, and use as a parameter for
                youtube-dl to fill in the rest of this YoutubeFile's members
        """
        self.url = url
        self.video_file_name = ""
        self.audio_file_name = ""
        self.length_in_seconds = 0
        self.logger = YoutubeDlLogger()

        # TODO: youtube-dl verifies URL isn't mailicious,
        #      such as a bash command, right?

        # For command-line options, see
        # https://github.com/ytdl-org/youtube-dl#options
        # For embedded options, see
        # .../youtube-dl/blob/master/youtube_dl/YoutubeDL.py
        youtube_dl_options = {
            # Do not download the video files
            "simulate" : True,
            # Do not print (most) messages to stdout
            "quiet" : True,
            # Force printing final filename
            "forcefilename" : True,
            # Force printing video length
            "forceduration" : True,
            # Do not allow "&" and spaces in file names
            "restrictfilenames" : True,
            # Catch youtube-dl output in a custom logger class
            "logger" : self.logger,
        }

        # Start youtube-dl with youtube_dl_options, unless self.url was invalid,
        # the output should be file name of the video
        with youtube_dl.YoutubeDL(youtube_dl_options) as ydl:
            try:
                ydl.download([self.url,])
            except youtube_dl.utils.DownloadError:
                # There was an issue accessing self.url, print verbose logs
                self.logger.print_log()
                return

        # The url was valid, set self.video_file_name and derive
        # self.audio_file_name from it (the same file name, but ending in .mp3)
        debug_messages = self.logger.get_messages("debug")
        self.video_file_name = debug_messages[1]
        index_of_last_period = self.video_file_name.rfind(".")
        self.audio_file_name = self.video_file_name[0:index_of_last_period] \
            + ".mp3"

        # Derive self.length_in_seconds from HH:MM:SS-like timestamp
        # Ex. 0:52 = 52 seconds
        # 3:21 = 3 minutes and 21 seconds
        # 50:24:46 = 50 hours, 24 minutes, and 46 seconds
        length_timestamp = debug_messages[2]
        length_timestamp = length_timestamp.split(":")
        hours = 0
        minutes = 0
        seconds = 0
        if len(length_timestamp) == 3:
            hours = int(length_timestamp[0])
            minutes = int(length_timestamp[1])
            seconds = int(length_timestamp[2])
        else:
            minutes = int(length_timestamp[0])
            seconds = int(length_timestamp[1])
        self.length_in_seconds = (hours * 60 * 60) + (minutes * 60) + seconds

    def download(self, directory : str) -> bool:
        """Download the YouTube video pointed to by self.url.

        Try to download the YouTube video pointed to by self.url to directory/
        self.audio_file_name. youtube-dl will take care of converting the video
        file to audio and restricting the allowed file size of the download.

        Args:
            self: This YoutubeFile
            directory: The directory to save the downloaded file into
        """
        # Clear logger
        self.logger = YoutubeDlLogger()

        # Try to download the video file
        # See https://github.com/ytdl-org/youtube-dl#options
        youtube_dl_options = {
            # Download format with best audio quality
            'format': 'bestaudio/best',
            # Location for youtube-dl to put cache files
            "cachedir" : directory,
            ##### This does not seem to actually work,
            ##### or causes issues with the postprocessor
            ##### Set the max allowed video size to 20MB
            ####"max_filesize" : "20m",
            # If the URL is of an item in a playlist, just download the
            # individual video instead of the playlist
            "noplaylist" : True,
            # Store the output file as directory/self.video_file_name before
            # post-processing
            "outtmpl" : f"{directory}/{self.video_file_name}",
            # Stop on download errors
            "ignoreerrors" : False,
            # In post-processing, turn video to mp3 via ffmpeg
            "postprocessors" : [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            # Do not keep the video file after post-processing 
            "keepvideo" : False,
            # Catch youtube-dl output in a custom logger class
            "logger" : self.logger,
        }
        
        # Start youtube-dl with youtube_dl_options, if everything went well
        # according to our options, youtube-dl will download the YouTube video
        # at self.url to directory/self.audio_file_name.
        with youtube_dl.YoutubeDL(youtube_dl_options) as ydl:
            try:
                ydl.download([self.url,])
            except youtube_dl.utils.DownloadError:
                # There was an issue downloading the video, print verbose logs
                self.logger.print_log()
                return False

        # There was no issue and the file was downloaded, return success
        return True

        

@youtube_slash_command_group.command(
    name="play",
    description="Play audio from YouTube video in voice chat.",
    checks=[
        ctx_check.assert_bot_is_in_voice_chat,
        ctx_check.assert_bot_is_in_same_voice_chat_as_author,
    ]
)
async def youtube_play(
    ctx,
    url: discord.Option(
        str,
        description="The URL of the video or playlist you wish to have played."
    )
):
    """Tell bot to play audio from a YouTube video or playlist in voice chat.

    Download the YouTube video(s) specified by url into cache, and play them in
    voice chat.

    Args:
        ctx: The context this SlashCommand was called under
        url: The URL for the YouTube video or playlist to download and play
    """
    # Check validity of URL
    if (not(url.startswith("https://youtu.be/") or \
        url.startswith("https://www.youtube.com/playlist?list="))):
        await ctx.respond(
            ephemeral=True,
            content="To play a single video, use a URL starting with " \
                + "`https://youtu.be/`, generated by the share button." \
                + "\nTo play a playlist, use a URL starting with " \
                + "`https://www.youtube.com/playlist?list=`, " \
                + "shown in your navigation bar when viewing the playlist " \
                + "(but not a specific video within it)." \
        )
        return False

    # Create empty list of files to be played
    youtube_file_list = []

    # Fill empty list, how many files to play will be determined by if the url
    # was a playlist or a single video
    youtube_file_list.append(YoutubeFile(url))
    #is_playlist = "/playlist?" in url
    #if is_playlist is False:
    #    youtube_file_list.append(YoutubeFile(url))
    #else:
    #    youtube_dl_options = {
    #        # Do not download the video and do not write anything to disk
    #        "simulate" : "",
    #        # Do not extract the videos of a playlist, only list them
    #        "flat-playlist" : "",
    #    }
    #    # Run youtube-dl with youtube_dl_options
    #    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
    #        ydl.download(url)

    # Tell the user to wait, downloads and file IO take time
    await ctx.respond(
        ephemeral=True,
        content="Please wait... trying to download the single video or " \
            + f"playlist pointed to by `{url}`. "
    )

    # Get AudioQueue cog
    audio_queue_list = ctx.bot.get_cog("AudioQueueList")

    # Download and queue all audio files
    rsp = ""
    for youtube_file in youtube_file_list:
        # If there was an issue getting information from youtube-dl for this
        # video, tell the author and don't bother downloading or queuing it
        if youtube_file.logger.had_error is True:
            rsp += f"\nError retrieving: `{youtube_file.url}`"
            continue

        if youtube_file.length_in_seconds > 30*60:
            rsp += f"\n{youtube_file.url} is longer than my max allowed " \
                + "video length of 30 minutes."
            continue

        # Download the audio file for this video if it's not already downloaded
        if youtube_file_cache.file_exists(youtube_file.audio_file_name) is False:
            # Download to intermediate cache, then move to youtube file cache
            if youtube_file.download(file_cache.CACHE_DIR) is False or \
                youtube_file_cache.add(youtube_file.audio_file_name) is False:
                rsp += f"\nError downloading: {youtube_file.url}"
                continue

        # Add the downloaded file to audio queue
        audio_queue_index = audio_queue_list.add(
            ctx = ctx,
            description = youtube_file.video_file_name,
            file_path = f"{youtube_file_cache.directory}/{youtube_file.audio_file_name}"
        )
        if audio_queue_index == -1:
            rsp += f"\nError queuing: {youtube_file.url}" \
                + "\nWill stop adding more audio to my audio queue."
            break
        else:
            rsp += f"\nSuccessfully queued: {youtube_file.url} " \
                + f"in slot `{audio_queue_index}`."

    # Tell author status of all downloading and queuing
    await ctx.respond(ephemeral=True, content=rsp)
    return True



#@spotify_slash_command_group.command(
#    name="play",
#    description="Play audio from Spotify in voice chat.",
#    checks=[
#        ctx_check.assert_bot_is_in_voice_chat,
#        ctx_check.assert_bot_is_in_same_voice_chat_as_author,
#    ]
#)
#async def spotify_play(
#    ctx,
#    url: discord.Option(
#        str,
#        description="The URL of the song or playlist you wish to have played."
#    )
#):
#    """Tell bot to play audio from a Spotify song or playlist in voice chat.
#
#    Download the YouTube video(s) specified by url into cache, and play them in
#    voice chat.
#
#    Args:
#        ctx: The context this SlashCommand was called under
#        url: The URL for the Spotify song or playlist to download and play
#    """
