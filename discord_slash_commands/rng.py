# ======================= #
# Import public libraries #
# ======================= #

# General discord API
import discord

# RNG API
import random

# =========================== #
# Define underlying structure #
# =========================== #

# Create slash command group
rng_slash_command_group = discord.SlashCommandGroup(
    checks = [assert_author_is_allowed_to_call_command],
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



# Define function for letting user roll a number
@rng_slash_command_group.command(name="roll", description="Roll a random number.")
async def rng_roll(
    ctx,
    is_whole: discord.Option(bool, description="Whether the number rolled should be whole."),
    minimum_value: discord.Option(float, description="The lowest number that can be rolled, inclusive."),
    maximum_value: discord.Option(float, description="The highest number that can be rolled, inclusive."),
):
    # Determine if the arguments are valid
    error_message = ""
    if maximum_value <= minimum_value:
        error_message += f"\nPlease give me a maximum value that is greater than the minimum value."
    if (maximum_value - minimum_value) < 1 and is_whole == True:
        error_message += f"\nI cannot roll a whole number between {minimum_value} and {maximum_value}."

    # If the user's arguments weren't valid, give them verbose error messages and an example to help them
    if error_message != "":
        error_message += f"\nHere's an example command."
        error_message += f"\nSimulate rolling a 6 sided-die by rolling a whole number between (and including) 1 and 6."
        error_message += f"\n`\\rng roll True 1 6`"
        await ctx.respond(ephemeral=True, content=error_message)
        return False

    # If we got here, the arguments are valid and safe to act upon
    # Send back a number matching their arguments
    if is_whole == True:
        await ctx.respond(ephemeral=False, content=str(random.randint(int(minimum_value), int(maximum_value))))
    else:
        await ctx.respond(ephemeral=False, content=str(round(minimum_value + (random.random() * (maximum_value - minimum_value)), 2)))
    return True



# Define function for letting user pick an option out of a list
@rng_slash_command_group.command(name="pick", description="Pick one or more random items from a list.")
async def rng_pick(
    ctx,
    number_of_items_to_pick: discord.Option(int, "The number of items allowed to be picked from the list."),
    repeats_allowed: discord.Option(bool, "Whether an item is allowed to be picked more than once."),
    items_to_pick_from: discord.Option(str, "A comma seperated list of items allowed to be picked.")
):
    # Split list, given as a monolithic comma-seperated string, into array elements
    items_to_pick_from = items_to_pick_from.split(",")

    # Determine if the arguments are valid
    error_message = ""
    if number_of_items_to_pick < 1:
        error_message += f"\nPlease give me a reasonable number of items to pick (more than 0)."
    if len(items_to_pick_from) < 2:
        error_message += f"\nPlease give me a reasonable number of items to choose from (more than 1)."
    if number_of_items_to_pick > len(items_to_pick_from) and repeats_allowed == False:
        error_message += f"\nCannot pick {number_of_items_to_pick} unique items from a list of {len(items_to_pick_from)} items."

    # If the user's arguments weren't valid, give them verbose error messages and an example to help them
    if error_message != "":
        error_message += f"\nHere's an example command."
        error_message += f"\nPick 2 different kind of juice to make popsicles from. The options are apple juice, orange juice, and grape juice."
        error_message += f"\n`\\rng pick 2 False \"apple juice, orange juice, grape juice\"`"
        await ctx.respond(ephemeral=True, content=error_message)
        return False
    
    # If we got here, the arguments are valid and safe to act upon
    # Make a list of items picked
    items_picked_list = []
    while number_of_items_to_pick > 0:
        index_of_item_picked = random.randint(0, len(items_to_pick_from) - 1)
        if repeats_allowed == True:
            items_picked_list.append(items_to_pick_from[index_of_item_picked])
        if repeats_allowed == False:
            items_picked_list.append(items_to_pick_from.pop(index_of_item_picked))
        number_of_items_to_pick -= 1

    # Give the user back the list of items picked
    items_picked_str = ""
    items_picked_str = items_picked_list.pop(0)
    while len(items_picked_list) > 0:
        items_picked_str += ", " + items_picked_list.pop(0)
    await ctx.respond(ephemeral=False, content=items_picked_str)
    return True
