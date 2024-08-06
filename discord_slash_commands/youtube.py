"""PyCord.SlashCommand for playing YouTube audio in voice chat.

This file defines slash commands for letting a member play audio from YouTube
videos in their current connected voice chat.
"""

#==============================================================================#
# Import public libraries                                                      #
#==============================================================================#

# Import regex API
import re

# Import interface to interact with YouTube
import youtube_dl

# Import Discord Python API
import discord

# Import functions for asserting bot state
import discord_slash_commands.helpers.application_context_checks as ctx_check

# Import helper for managing new files
from discord_slash_commands.helpers import file_cache

# Import helper for queueing audio in voice chat
from discord_slash_commands.helpers import audio_queue

# Import user permissions for each guild
import discord_slash_commands.helpers.user_permission as user_perm

#==============================================================================#
# Define underlying structure                                                  #
#==============================================================================#

# Create instance of file cache for Youtube audio files
youtube_file_cache = file_cache.FileCacheList(
    directory = "youtube",
    max_bytes = 100 * 1000000
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
class YoutubeDlLogger():
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

    def warning(self, message) -> None:
        """Handler for when youtube-dl throws a warning message.

        Log a warning message thrown by youtube-dl.

        Args:
            self: This YoutubeDlLogger
            message: The message thrown by youtube-dl
        """
        self.message_list.append(("warning", message))

    def error(self, message) -> None:
        """Handler for when youtube-dl throws an error message.

        Log an error message thrown by youtube-dl. Log that an error occured.

        Args:
            self: This YoutubeDlLogger
            message: The message thrown by youtube-dl
        """
        self.message_list.append(("error", message))
        self.had_error = True

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
            pointed to by it, stripped of non-ASCII characters.
        audio_file_name: video_file_name, but with an mp3 file type instead
        length_in_seconds: An integer containing the length of the YouTube video
            pointed to by url, in seconds.
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

        # NOTE: Seems like youtube-dl doesn't allow malicious URL,
        # such as a bash commands, not 100% sure though

        # For command-line options, see
        # https://github.com/ytdl-org/youtube-dl#options
        # For embedded options, like below, see
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
        self.length_in_seconds = audio_queue.timestamp_to_seconds(
            debug_messages[2]
        )

    def download(self, directory : str) -> bool:
        """Download the YouTube video pointed to by self.url.

        Try to download the YouTube video pointed to by self.url to
        directory/self.audio_file_name. youtube-dl will take care of converting
        the video file to pure audio and restricting the allowed video length
        of the download.

        Args:
            self: This YoutubeFile
            directory: The directory to save the downloaded file into
        """
        # Clear logger
        self.logger = YoutubeDlLogger()

        # Try to download the video file
        # For command-line options, see
        # https://github.com/ytdl-org/youtube-dl#options
        # For embedded options, like below, see
        # .../youtube-dl/blob/master/youtube_dl/YoutubeDL.py
        youtube_dl_options = {
            # Download format with best audio quality
            'format': 'bestaudio/best',
            # Location for youtube-dl to put cache files
            "cachedir" : directory,
            ##### This does not seem to actually work,
            ##### or causes issues with the postprocessor
            ##### Set the max allowed video size to 20MB
            ####"max_filesize" : "20m",
            # Number of times to retry for HTTP error 5xx
            "retries": 5,  
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

    def queue(self, audio_queue_list : discord.Cog, normalize : bool, ctx) -> str:
        """

        Returns:
            Status message.
        """
        # If there was an issue getting information from youtube-dl for this
        # video, tell the author and don't bother downloading or queuing it
        if self.logger.had_error is True:
            return f"\nError retrieving: {self.url}"

        # If even before downloading the video, we can see it's over 30 minutes
        # long, deny downloading/playing it, and tell author why
        if self.length_in_seconds > 30*60:
            return f"\nRefusing to download: {self.url}, it's longer max allowed video length of 30 minutes."

        # Download the audio file for this video if it's not already downloaded to intermediate cache, then move to youtube file cache
        # TODO: Use different thread to download and queue audio?
        #       Could that cause deletion issues?
        # TODO: with the addition of the normalize option, it's possible the predownloaded audio won't have matching normalization
        if not youtube_file_cache.file_exists(self.audio_file_name) and \
            (
                self.download(file_cache.CACHE_DIR) is False or \
                youtube_file_cache.add(
                    file_name = self.audio_file_name,
                    normalize_audio = normalize
                ) is False
            ):
            return f"\nError downloading: {self.url}"

        # Add the downloaded file to audio queue
        audio_queue_element_id = audio_queue_list.add(
            ctx = ctx,
            description = self.video_file_name,
            file_path = f"{youtube_file_cache.directory}/" \
                + f"{self.audio_file_name}",
            priority = audio_queue.LOW_PRIORITY
        )
        if audio_queue_element_id == -1:
            return f"\nError queuing: {self.url}"

        # Audio was sucessfully added to queue
        num_files_ahead = audio_queue_list.get_index_in_queue(
            audio_queue_element_id = audio_queue_element_id,
            priority = audio_queue.LOW_PRIORITY
        )
        return f"\nSuccessfully queued: {self.url} as ID " \
            + f"`{audio_queue_element_id}`." \
            + f"\nThere are `{num_files_ahead}` other low-priority (priority " \
            + f"level `{audio_queue.LOW_PRIORITY}`) audio files ahead of you."



@youtube_slash_command_group.command(
    name="play",
    description="Make me play audio of a single YouTube video in voice chat.",
    checks=[
        ctx_check.assert_bot_is_in_voice_chat,
        ctx_check.assert_bot_is_in_same_voice_chat_as_author,
    ]
)
async def youtube_play(
    ctx,
    url: discord.Option(
        str,
        description="The URL of the YouTube video you wish to have played."
    ),
    # TODO: add optional start timestamp to command
    #timestamp: discord.Option(
    #    str,
    #    description="At what timestamp to start playing the audio."
    #    default="0:00:00"
    #),
    normalize: discord.Option(
        bool,
        description="Make volume more consistent throughout audio.",
        default=False
    )
):
    """Tell bot to play audio from single YouTube video in voice chat.

    Download the YouTube video specified by url into cache, and play them in
    voice chat.

    Args:
        ctx: The context this SlashCommand was called under
        url: The URL for the YouTube video or playlist to download and play
        normalize: Make the volume more consistent throughout the audio
    """
    # If the URL came from someone's URL bar, reformat it to make API happy
    # by removing all GET parameters but v, which gives the video ID
    if url.startswith("https://www.youtube.com/"):
        # Find the video ID, which is Base 64 + '-' and '_'
        # https://en.wikipedia.org/wiki/Base64
        match = re.findall(
            pattern="v=[A-Z,a-z,0-9,+/=-_]+",
            string=url
        )
        # Reformat the video URL to just be youtube + the video ID
        if len(match) > 0:
            url = "https://youtu.be/" + match[0][2:]

    # Check validity of URL
    if not url.startswith("https://youtu.be/"):
        await ctx.respond(
            ephemeral=True,
            content="Please use a YouTube link with the video ID included.\n"
                + "The URL generated by the 'Share' button should be " \
                + "guarateed to have this."
        )
        return False

    # Tell the user to wait, downloads and file IO take time
    await ctx.respond(
        ephemeral=True,
        content=f"Downloading the video pointed to by `{url}`..."
    )

    # Download/queue audio
    youtube_file = YoutubeFile(url=url)
    await ctx.respond(
        ephemeral=True,
        content=youtube_file.queue(
            audio_queue_list=ctx.bot.get_cog("AudioQueueList"),
            normalize=normalize,
            ctx=ctx
        )
    )
    return True



@youtube_slash_command_group.command(
    name="playlist",
    description="Make me play audio of a YouTube playlist in voice chat.",
    checks=[
        ctx_check.assert_bot_is_in_voice_chat,
        ctx_check.assert_bot_is_in_same_voice_chat_as_author,
    ]
)
async def youtube_playlist(
    ctx,
    url: discord.Option(
        str,
        description="The URL of the YouTube playlist you wish to have played."
    ),
    # TODO: add options for order and indexes
    normalize: discord.Option(
        bool,
        description="Make volume more consistent throughout audio.",
        default=False
    )
):
    """Tell bot to play audio from a YouTube playlist in voice chat.

    Download the YouTube videos specified by url into cache, and play them in
    voice chat.

    Args:
        ctx: The context this SlashCommand was called under
        url: The URL for the YouTube playlist to download and play
        normalize: Make the volume more consistent throughout the audio
    """
    if ctx.author.id == user_perm.get_bot_owner_discord_user_id() == False:
        await ctx.respond(
            ephemeral=True,
            content="This command is in alpha!\n"
                + "Please let the bot owner know any issues you have!"
        )

    # The playlist format must follow:
    #   https://www.youtube.com/...list=list_ID
    # And the playlist must be made unlisted or public,
    # using the page pointed to by
    #   https://www.youtube.com/playlist?list=list_ID
    # https://github.com/ytdl-org/youtube-dl/issues/32814

    # Check validity of URL
    #if not url.startswith("https://www.youtube.com/playlist?list=")):
    #    await ctx.respond(
    #        ephemeral=True,
    #        content="To play a single video, use a URL starting with " \
    #            + "`https://youtu.be/`, generated by the share button." \
    #            + "\nTo play a playlist, use a URL starting with " \
    #            + "`https://www.youtube.com/playlist?list=`, " \
    #            + "shown in your navigation bar when viewing the playlist " \
    #            + "(but not a specific video within it)." \
    #    )
    #    return False

    # Create empty list of files to be played
    youtube_file_list = []

    # Tell the user to wait, downloads and file IO take time
    await ctx.respond(
        ephemeral=True,
        content=f"Downloading the playlist pointed to by `{url}`..."
    )

    # Get every video to download
    logger = YoutubeDlLogger()
    youtube_dl_options = {
        # Do not download the video files
        "simulate" : True,
        # TODO
        "noplaylist" : False,
        # Do not extract the videos of a playlist, only list them
        #"extract_flat" : True,
        # Do not print (most) messages to stdout
        "quiet" : True,
        # Catch youtube-dl output in a custom logger class
        "logger" : logger,
    } 
    with youtube_dl.YoutubeDL(youtube_dl_options) as ydl:
        try:
            print(url)
            ydl.download([url,])
        except youtube_dl.utils.DownloadError:
            # There was an issue accessing self.url, print verbose logs
            logger.print_log()
            return False

    # Output looks like:
    # debug: [youtube:tab] Downloading playlist PL9_sHyydmMlf4RWuc0tWKkOF9xvxvmWET - add --no-playlist to just download video Oud9Gzy89dw
    # debug: [youtube:tab] PL9_sHyydmMlf4RWuc0tWKkOF9xvxvmWET: Downloading webpage
    # debug: [download] Downloading playlist: chill
    # debug: [youtube:tab] playlist chill: Downloading 14 videos
    # debug: [download] Downloading video 1 of 14
    # debug: [youtube] Oud9Gzy89dw: Downloading webpage
    # debug: [download] Downloading video 2 of 14      
    # debug: [youtube] BEcHG4cRILI: Downloading webpage
    # ...
    # debug: [download] Finished downloading playlist: chill

    logger.print_log()

    # Create list of video ids
    debug_messages = logger.get_messages("debug")
    num_videos = int(re.findall(pattern="[0-9]+", string=debug_messages[3])[0])
    video_id_list = []
    for i in range(num_videos):
        line = debug_messages[5 + (i * 2)]
        video_id_list.append(line.split()[1][:-1])

    # Download/queue audio
    # TODO: only print status if there was issue to void clutter, say when done after loop is done
    for video_id in video_id_list:
        youtube_file = YoutubeFile(url="https://youtu.be/" + video_id)
        await ctx.respond(
            ephemeral=True,
            content=youtube_file.queue(
                audio_queue_list=ctx.bot.get_cog("AudioQueueList"),
                normalize=normalize,
                ctx=ctx
            )
        )

    await ctx.respond(ephemeral=True, content="Done!")

    return True
