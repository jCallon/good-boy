"""PyCord.SlashCommand for getting random numbers and decisions.

This file defines slash commands for letting a member make decisions using
random number generation.
"""

#==============================================================================#
# Import libraries                                                             #
#==============================================================================#

# Import RNG API
import random

# Import Discord Python API
import discord

# Custom functions for denying commands based off of bot state
import discord_slash_commands.helpers.application_context_checks as ctx_check

#==============================================================================#
# Define underlying structure                                                  #
#==============================================================================#

# Create RNG slash command group
rng_slash_command_group = discord.SlashCommandGroup(
    checks = [ctx_check.assert_author_is_allowed_to_call_command],
    #default_member_permissions = default,
    description = "Random number generation commands",
    #description_localizations = default,
    #guild_ids = default,
    guild_only = False,
    name = "rng",
    #name_localizations = default,
    #nsfw = default,
    #parent = default
)



@rng_slash_command_group.command(
    name="roll",
    description="Roll a random number."
)
async def rng_roll(
    ctx,
    is_whole: discord.Option(
        bool,
        description="Whether the number rolled should be whole."
    ),
    min_value: discord.Option(
        float,
        description="The lowest number allowed to be rolled, inclusive."
    ),
    max_value: discord.Option(
        float,
        description="The highest number allowed to be rolled, inclusive."
    ),
):
    """Tell bot to give you a random number.

    Make the bot give you back a random number, between and including
    minimum_valie and max_value. The number given back will be an integer
    if is_whole, otherwise a float.

    Args:
        ctx: The context this SlashCommand was called under
        is_whole: Whether the result should be an integer ot float
        min_value: The smallest value, inclusive, allowed to be rolled
        min_value: The largest value, inclusive, allowed to be rolled
    """
    # Determine if the author's arguments are valid
    err_msg = ""
    if max_value <= min_value:
        err_msg += "\nPlease give a max_value > min_value."
    if (max_value - min_value) < 1 and is_whole is True:
        err_msg += "\nI cannot roll >1 value from these arguments."

    # If the author's arguments were invalid,
    # give them verbose error messages and an example to help them
    if err_msg != "":
        err_msg += "\nHere's an example command."
        err_msg += "\nSimulate rolling a 6 sided-die."
        err_msg += "\n`/rng roll is_whole: true min_value: 1 max_value: 6`"
        await ctx.respond(ephemeral=True, content=err_msg)
        return False

    # If we got here, the arguments are valid and safe to act upon
    # Send back a number matching their arguments
    random_number = 0
    if is_whole is True:
        random_number = random.randint(int(min_value), int(max_value))
    else:
        random_number = min_value + (random.random() * (max_value - min_value))
        random_number = round(random_number, 2)
    await ctx.respond(ephemeral=False, content=random_number)
    return True



# Define function for letting user pick an option out of a list
@rng_slash_command_group.command(
    name="pick",
    description="Pick one or more random items from a list."
)
async def rng_pick(
    ctx,
    num_results: discord.Option(
        int,
        "The number of items you expect in your result."
    ),
    allow_repeats: discord.Option(
        bool,
        "Whether an item is allowed to be picked more than once."
    ),
    options: discord.Option(
        str,
        "A comma seperated list of items allowed to be picked."
    )
):
    """Tell bot to pick items from a list for you.

    Make the bot pick num_results items from your options. If allow_repeats,
    the same item may be picked from your options more than once.

    Args:
        ctx: The context this SlashCommand was called under
        num_results: The number of items that should be picked by the end
        allow_repeats: Whether an item may be picked multiple times
        options: The string holding a comma-seperated list of items to pick from
    """
    # Split monolithic comma-seperated string of options into list
    options = options.split(",")

    # Determine if the author's arguments are valid
    err_msg = ""
    if num_results < 1:
        err_msg += "\nPlease use num_results > 0."
    if len(options) < 2:
        err_msg += "\nPlease have >1 item in your options."
    if num_results > len(options) and allow_repeats is False:
        err_msg += f"\nCan't pick {num_results} unique items from your options."

    # If the author's arguments were invalid,
    # give them verbose error messages and an example to help them
    if err_msg != "":
        err_msg += "\nHere's an example command."
        err_msg += "\nPick 2 different kind of juice to make popsicles from."
        err_msg += "\n`/rng pick num_results: 2 allow_repeats: false "
        err_msg += "options: apple juice,orange juice,grape juice`"
        await ctx.respond(ephemeral=True, content=err_msg)
        return False

    # If we got here, the arguments are valid and safe to act upon
    # Make a list of items picked
    result = []
    while num_results > 0:
        index_of_item_picked = random.randint(0, len(options) - 1)
        result.append(options[index_of_item_picked])
        if allow_repeats is False:
            options.pop(index_of_item_picked)
        num_results -= 1

    # Give the user back the list of items picked
    await ctx.respond(ephemeral=False, content=', '.join(result))
    return True
