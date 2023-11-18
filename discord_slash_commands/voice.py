"""PyCord.SlashCommand for altering PyCord Discord bot voice state.

This file defines slash commands for letting a member connect, disconnect, or
otherwise modify the voice state of the bot. These slash commands don't do much
themselves, but enable all other slash commands used by the bot that play or
otherwise interface with audio in voice chat.
"""

#==============================================================================#
# Import public libraries                                                      #
#==============================================================================#

# Import Discord Python API
import discord

# Import functions for asserting bot state
import discord_slash_commands.helpers.application_context_checks as ctx_check

# Import Discord extended APIs to create organized lists
from discord.ext import pages

# TODO: write comment
from discord_slash_commands.helpers import audio_queue

#==============================================================================#
# Define underlying structure                                                  #
#==============================================================================#

# NOTE: This bot currently only supports being in one voice chat at a time,
# and all coding of this bot assumes this.



# Create voice slash command group
voice_slash_command_group = discord.SlashCommandGroup(
    checks = [ctx_check.assert_author_is_allowed_to_call_command],
    #default_member_permissions = default,
    description = "Voice state commands",
    #description_localizations = default,
    #guild_ids = default,
    guild_only = True,
    name = "voice",
    #name_localizations = default,
    #nsfw = default,
    #parent = default
)



@voice_slash_command_group.command(
    name="join",
    description="Make me join your voice chat.",
    checks=[ctx_check.assert_bot_is_not_in_voice_chat]
)
async def voice_join(ctx):
    """Tell bot to join your voice chat.

    Connects bot to message author's voice chat, if bot is not already in a
    voice chat, and the message author is in a valid voice chat to join.

    Args:
        ctx: The context this SlashCommand was called under
    """
    # We join the author's voice chat, if they aren't in one, we can't act
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.respond(
            ephemeral = True,
            content = "Please join a voice chat. I join the chat you are in."
        )
        return False

    # Join the author's voice chat
    await ctx.author.voice.channel.connect()
    ctx.bot.add_cog(audio_queue.AudioQueueList(ctx.bot.voice_clients[0]))
    await ctx.respond(
        ephemeral = False,
        delete_after = 60*30,
        content = "I have tried to connect to your voice channel."
    )
    return True



@voice_slash_command_group.command(
    name="leave",
    description="Make me leave your voice chat.",
    checks=[
        ctx_check.assert_bot_is_in_voice_chat,
        ctx_check.assert_bot_is_in_same_voice_chat_as_author,
        ctx_check.assert_bot_is_not_playing_audio_in_voice_chat,
    ]
)
async def voice_leave(ctx):
    """Tell bot to leave your voice chat.

    Disconnect the bot from your voice chat if it's not busy playing audio.

    Args:
        ctx: The context this SlashCommand was called under
    """
    # Leave the author's voice chat
    await ctx.voice_client.disconnect()
    ctx.bot.remove_cog("AudioQueueList")
    await ctx.respond(
        ephemeral=False,
        delete_after=60*30,
        content="I have tried to disconnect from your voice channel."
    )
    return True



#@voice_slash_command_group.command(
#    name="volume",
#    description="TODO.",
#    checks=[]
#)
#async def voice_volume(ctx):
#    """TODO.
#
#    TODO.
#
#    Args:
#        ctx: The context this SlashCommand was called under
#        TODO
#    """
#    # TODO
#    await ctx.respond(ephemeral=True, content="")
#    return True



voice_queue_slash_command_group = voice_slash_command_group.create_subgroup(
    name="queue",
    description = "Voice/audio queue commands",
    #guild_ids = default,
    guild_only = True,
    #nsfw = default,
    #default_member_permissions = default,
    checks = [
        ctx_check.assert_bot_is_in_voice_chat,
        ctx_check.assert_bot_is_in_same_voice_chat_as_author,
        ctx_check.assert_bot_audio_queue_length_is_non_zero,
    ],
    #name_localizations = default,
    #description_localizations = default,
)



@voice_queue_slash_command_group.command(
    name="remove",
    description="Skip playing a certain item in the audio queue.",
)
async def voice_queue_remove(
    ctx,
    audio_queue_element_id: discord.Option(
        int,
        description="ID of audio queue item to skip. " \
            "Leave blank to skip top of queue.",
        default=None
    )
):
    """Tell bot to remove a certain item from its audio queue.

    Make bot remove the audio queue element specified by audio_queue_element_id
    from its audio queue. If None is provided, remove the top of the audio
    queue, effectively skipping whatever is currently playing or will play next.

    Args:
        ctx: The context this SlashCommand was called under
        audio_queue_element_id: The audio_queue_element_id of the
            AudioQueueElement to remove from audio_queue
    """
    # Get the audio queue,
    # fill in the audio_queue_element_id if None was provided
    audio_queue_list = bot.ctx.cogs.get_cog("AudioQueueList")
    if audio_queue_element_id is None:
        audio_queue_element_id = audio_queue_list.queue[0].audio_queue_element_id

    # Try to remove audio_queue_element_id from audio_queue
    if audio_queue_list.remove(audio_queue_element_id) is False:
        await ctx.respond(
            ephemeral=True,
            content="I could not find an item in the audio queue with an ID " \
                + f"of {audio_queue_element_id}."
        )
        return False
        
    await ctx.respond(
        ephemeral=False,
        delete_after=60,
        content="I removed the audio queue item with an ID of " \
            + f"{audio_queue_element_id} from my audio queue."
    )
    return True



@voice_queue_slash_command_group.command(
    name="pause",
    description="Pause or unpause my audio queue.",
)
async def voice_queue_pause(
    ctx,
    value: discord.Option(
        str,
        description="Whether to start or stop pausing.",
        choices=["start", "stop"]
    )
):
    """Pause or unpause playing audio in voice chat.

    If starting pause, stop playing audio in voice chat, with the intent to
    resume the same audio queue, possibly modified, later, from the same spot,
    if possible. If stopping pause, resume playing audio from the point it was
    paused, if available, otherwise just what's at the top of audio queue.

    Args:
        ctx: The context this SlashCommand was called under
        value: Whether to start or stop pausing audio queue
    """
    # Get the audio queue, set whether to pause or unpause it
    audio_queue_list = bot.ctx.cogs.get_cog("AudioQueueList")
    if value == "start":
        audio_queue_list.pause()
        await ctx.respond(ephemeral=True, content="I paused my audio queue.")
    elif value == "stop":
        audio_queue_list.unpause()
        await ctx.respond(ephemeral=True, content="I unpaused my audio queue.")

    return True



@voice_queue_slash_command_group.command(
    name="list",
    description="List what's currently in my audio queue.",
)
async def voice_queue_list(ctx):
    """Tell bot to list audio queue.

    Tell the bot to give you a list and details of all its audio queue elements.

    Args:
        ctx: The context this SlashCommand was called under
    """
    # Get the audio queue
    audio_queue_list = ctx.bot.get_cog("AudioQueueList")

    # Make a list of strings, each list element afer the 1st representing an
    # AudioQueueElement
    page_list = ["Summary:" \
        + "\n`Audio Queue Element ID: First 50 characters of description`"]
    for audio_queue_element in audio_queue_list.queue:
        page_list[0] += f"\n`{audio_queue_element.audio_queue_element_id}: " \
            + f"{audio_queue_element.description[:49]}`"
        page_list.append(audio_queue_element.to_str())

    # Return a neat page view of the audio queue
    paginator = pages.Paginator(pages=page_list, loop_pages=False)
    await paginator.respond(ctx.interaction, ephemeral=True)
    return True
