"""TODO.

TODO.
"""

#==============================================================================#
# Import libraries                                                             #
#==============================================================================#

#==============================================================================#
# Define underlying structure                                                  #
#==============================================================================#

# Create an ad-hoc way to queue audio one-after-another
# TODO: make real audio queue, this pains me

global next_voice_client: discord.VoiceClient
global next_audio_source: discord.AudioSource
global next_after_function: Callable
next_voice_client = None
next_audio_source = None
next_after_function = None

def set_next_source(
    voice_client: discord.VoiceClient,
    audio_source: discord.AudioSource,
    after_function: Callable
) -> None:
    """Set variables used on the next call of play_next_audio_queue_source.

    Set the global variables that will be used as arguments, sources, etc. in
    the next play_next_audio_queue_source call. That function, intended to be
    used as an after function of PyCord.VoiceClient.play(), is not allowed to
    have any parameters but error, so globals are the only option I see for now.

    Args:
        voice_client: The voice client play_next_audio_queue_source will play
            audio on
        audio_source: The audio source play_next_audio_queue_source will play
        after_function: The function play_next_audio_queue_source will call
            when it is done playing audio_source
    """
    global next_voice_client
    global next_audio_source
    global next_after_function
    next_voice_client = voice_client
    next_audio_source = audio_source
    next_after_function = after_function

def play_next_source(error) -> None:
    """Using some globals, make a VoiceClient.play() call.

    Use next_voice_client to play next_audio_source, and after that is done,
    call next_after_function.

    Args:
        error: Any errors that happened during the previous VoiceClient.play()
    """
    if error != None:
        print(error)
    next_voice_client.play(next_audio_source, after=next_after_function)
