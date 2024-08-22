from email import message
import discord
from discord import app_commands
from player import Player
import ast
import traceback
guildID = input("GuildID: ")

intents = discord.Intents.default()

intents.messages = True
intents.message_content = True
client = discord.Client(intents = intents)
tree = app_commands.CommandTree(client)

@tree.command(guild=discord.Object(id=guildID))
async def help(interaction: discord.Interaction):
    await interaction.response.send_message(
        """Welcome to Hereditus, a strategy game featuring genetics, combat, and colony building.
        To join, wait for a game to be created, and join using the command /join before it starts.
        Once the game starts, if you aren't in the game already, you won't be able to join.
        If you did join the game, start by running /colony_info, to see the stats of your initial generation (gen0) Torbs.
        Torbs are your Colony's inhabitants, and are very simple creatures, they eat one morsel of food per year, and can only do one other activity per year.
        The activities your Torbs will do is your choice, assign Torbs to breed using /breed, to fight using /enlist, , if they aren't assigned to either of those activities, or gather food for the colony.
        When selecting Torbs, use the format '00-01' to select the Torb from generation 0, and ID 1.
        To pair Torbs for breeding, list the Torbs in /breed in the order you want them to be paired, the first torb will be paired with the second, the third with the fourth, etc. Use commas, semi-colons or any characters other than hyphens and numbers to separate them if you wish.
        (i.e. 00-00, 00-01, 00-02, 00-03) will breed Torbs 00-00 and 00-01 together, and Torbs 00-02, 00-03.
        If you have Torbs enlisted, you can use /scout to get an idea of how the other colonies compare to yours.
        If a Torb is injured, it can be instructed to rest using /rest, where it will heal 3 hp.
        Any Torbs not enlisted, assigned to breeding, or resting, will gather food.
        At the end of each year, Torbs have a colony meal where they will starve and take 1hp damage if there's not enough food for them, or heal 1hp if there is enough food.
        """,ephemeral=True)
    return

@tree.command(guild=discord.Object(id=guildID))
async def commands(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"""Commands available:
        /join [Desired Colony Name] (If a game is available to join)
        /colony_info (Returns info on Colony, and Torbs)
        /breed [Torbs to be bred] (Use form 00-01, 00-02; 00-03, 00-04 or similar, only the order of Torbs matters, not punctuation)
        /scout (Returns info on other colonies)
        /ready (Tells the game that you are ready for the next round)
        /help
        /commands
        /rest
        /enlist
        /discharge""", ephemeral = True)
    return

@tree.command(guild=discord.Object(id=guildID))
async def new(interaction: discord.Interaction):
    from simulator import Simulator
    a = Simulator(Simulator._next_SID)
    a.new_evolution_engine()
    await interaction.response.send_message(f"New game available!\nRun /join to join the game, then wait for the game to start.")
    return

@tree.command(guild=discord.Object(id=guildID))
async def ai_player(interaction: discord.Interaction, num_ai: int):
    from ai_player import AIPlayer
    try:
        new_ai = AIPlayer()
        new_ai.create_colonies(num_ai)
        await interaction.response.send_message(f"AIs generated.", ephemeral=True)
        return
    except Exception as e:
        error_type = type(e).__name__
        error_traceback = traceback.format_exc()
        print(error_traceback)  # or save it to a log file
        await interaction.response.send_message(f"Error ({error_type}): {e}")
    return

@tree.command(guild=discord.Object(id=guildID))
async def start(interaction: discord.Interaction, num_torbs: int):
    from simulator import Simulator
    from colony import Colony
    try:
        Simulator._instances[0].init_all_colonies(num_torbs)
    except KeyError:
        await interaction.response.send_message(f"Command Invalid: Invalid Game ID")
        return
    await interaction.response.send_message(
        f"""{len(Colony._instances)} Colonies initialized, the game has started.
        Run /commands to see available commands and /help for help.""")
    return

@tree.command(guild=discord.Object(id=guildID))
async def join(interaction: discord.Interaction, colony_name: str):
    if len(colony_name) > 16:
        await interaction.response.send_message("Invalid Colony Name: Name must be 16 characters or fewer")
        return
    elif not colony_name.isalnum():
        await interaction.response.send_message("Invalid Colony Name: Name must have only letters and numbers")
        return
    
    from simulator import Simulator
    
    try:
        if Simulator._instances[0].started:
            await interaction.response.send_message("Sorry, the game already started. This game has late-join disabled.",ephemeral=True)
            return
        if interaction.user.id in Player._instances.items():
            await interaction.response.send_message("Command Invalid: You have already joined this game.",ephemeral=True)
            return
        else:
            if type(interaction.user.nick) != str:
                player_name = interaction.user.name
            else:
                player_name = interaction.user.nick
            print(f"New Player requested: {player_name}")
            a = Player(interaction.user.id, name = player_name)
            
        Simulator._instances[0].new_colony(name = colony_name, EEID = 0, PID = interaction.user.id)
        from story_strings import player_strings
        await interaction.response.send_message(f"Colony generated! Welcome to the game, {player_strings(player_name)}!",ephemeral=True)
        await interaction.followup.send(f"{player_name} joined the game!")
        
    except KeyError:
        await interaction.response.send_message(f"Command Invalid: Invalid Game ID")
    return

@tree.command(guild=discord.Object(id=guildID))
async def breed(interaction: discord.Interaction, breeding_pairs: str):
    try:
        player_instance = Player._instances[interaction.user.id]
        first_colony_key = list(player_instance.colonies.keys())[0]
        player_instance.call_colony_reproduction(first_colony_key, breeding_pairs)
        await interaction.response.send_message(f"Torbs bred. Run /colony_info to see torbs", ephemeral = True)
        return
    except Exception as e:
        error_type = type(e).__name__
        error_traceback = traceback.format_exc()
        print(error_traceback)  # or save it to a log file
        await interaction.response.send_message(f"Error ({error_type}): {e}")
    return

@tree.command(guild=discord.Object(id=guildID))
async def next(interaction: discord.Interaction):
    try:
        from simulator import Simulator
        combat_str, new_year = Simulator._instances[0].next_round()
        await interaction.response.send_message(f"{combat_str}\nIt is now year {new_year}.\n")
    except Exception as e:
        error_type = type(e).__name__
        error_traceback = traceback.format_exc()
        print(error_traceback)  # or save it to a log file
        await interaction.response.send_message(f"Error ({error_type}): {e}")
    return
@tree.command(guild=discord.Object(id=guildID))
async def ready(interaction: discord.Interaction):
    player_instance = Player._instances[interaction.user.id]
    first_colony_key = list(player_instance.colonies.keys())[0]
    
    if player_instance.colonies[first_colony_key].ready:
        await interaction.response.send_message(f"Your colony is as ready as it can be already.", ephemeral=True)
    
    ready_message = player_instance.ready_up(player_instance.colonies[first_colony_key].CID)
    await interaction.response.send_message(f"{ready_message}", ephemeral = True)
    from story_strings import ready_message
    await interaction.followup.send(f":ballot_box_with_check: {ready_message(player_instance.name)}")
    return

@tree.command(guild=discord.Object(id=guildID))
async def force_ready(interaction: discord.Interaction):
    from simulator import Simulator
    Simulator._instances[0].ready_all()
    await interaction.followup.send(f"All colonies were force-set ready.")
    return

@tree.command(guild=discord.Object(id=guildID))
async def scout(interaction: discord.Interaction):
    try:
        player_instance = Player._instances[interaction.user.id]
        first_colony_key = list(player_instance.colonies.keys())[0]
        scout_report = player_instance.scout_all(player_instance.colonies[first_colony_key].CID)
        await interaction.response.send_message(f"{scout_report}", ephemeral = True)
        return
    except Exception as e:
        error_type = type(e).__name__
        error_traceback = traceback.format_exc()
        print(error_traceback)  # or save it to a log file
        await interaction.response.send_message(f"Error ({error_type}): {e}")
    return

@tree.command(guild=discord.Object(id=guildID))
async def attack(interaction: discord.Interaction, target_colony_name: str):
    player_instance = Player._instances[interaction.user.id]
    first_colony_key = list(player_instance.colonies.keys())[0]
    set_target_success  = player_instance.set_target(player_instance.colonies[first_colony_key].CID, target_colony_name)
    if set_target_success:
        await interaction.response.send_message(f"We will plan on attacking {target_colony_name}", ephemeral = True)
    else:
        await interaction.response.send_message(f"Error: Colony not found", ephemeral = True)
    return

@tree.command(guild=discord.Object(id=guildID))
async def enlist(interaction: discord.Interaction, torbs: str):
    try:
        player_instance = Player._instances[interaction.user.id]
        first_colony_key = list(player_instance.colonies.keys())[0]
        num_torbs_training = player_instance.train_soldiers(first_colony_key, torbs)
        await interaction.response.send_message(f"{num_torbs_training} Torbs are on the path to becoming soldiers.", ephemeral = True)
        return
    except Exception as e:
        error_type = type(e).__name__
        error_traceback = traceback.format_exc()
        print(error_traceback)  # or save it to a log file
        await interaction.response.send_message(f"Error ({error_type}): {e}")
    return

@tree.command(guild=discord.Object(id=guildID))
async def discharge(interaction: discord.Interaction, torbs: str):
    player_instance = Player._instances[interaction.user.id]
    first_colony_key = list(player_instance.colonies.keys())[0]
    num_soldiers, num_training = player_instance.discharge_soldiers(first_colony_key, torbs)
    await interaction.response.send_message(f"You have {num_soldiers} soldiers remaining, with {num_training} in training.", ephemeral = True)
    return

@tree.command(guild=discord.Object(id=guildID))
async def funerals(interaction: discord.Interaction):
    player_instance = Player._instances[interaction.user.id]
    player_instance.hide_dead = True
    await interaction.response.send_message(f"Your Torbs will start preparing funerals, and you will no longer see Dead Torbs in colony_info.", ephemeral = True)
    return

@tree.command(guild=discord.Object(id=guildID))
async def remembrance(interaction: discord.Interaction):
    player_instance = Player._instances[interaction.user.id]
    player_instance.hide_dead = False
    await interaction.response.send_message(f"Your Torbs will stop preparing funerals and remember Dead Torbs in colony_info.", ephemeral = True)
    return

@tree.command(guild=discord.Object(id=guildID))
async def colony(interaction: discord.Interaction):
    print("Trying discord command colony_info")
    try:
        player_instance = Player._instances[interaction.user.id]
        print(f"{interaction.user.id}")
        from simulator import Simulator
        if Simulator._instances[0].started == False:
            await interaction.response.send_message("The game hasn't started yet.\nPlease wait for an admin to start the game.")
            return
        if player_instance.colonies:
            first_colony_key = list(player_instance.colonies.keys())[0]
            print(first_colony_key)
            gen_strings = []
            for i in range(0, player_instance.colonies[first_colony_key].generations+1):
                gen_strings.append(player_instance.view_torbs(player_instance.colonies[first_colony_key].CID, i))
            #torb_string = player_instance.view_torbs(player_instance.colonies[first_colony_key])
            group_sizes = [1, 5, 4, 3, 2]  # Define the group sizes
            start_index = 0  # Starting index for each group

            for group_size in group_sizes:
                # Accumulate messages for the current group
                message = "".join(gen_strings[start_index:start_index + group_size])
                
                # Send the message
                if start_index == 0:
                    await interaction.response.send_message(message, ephemeral=True)
                elif message != "":
                    await interaction.followup.send(message, ephemeral=True)

                # Update the start index for the next group
                start_index += group_size

            # Send remaining messages individually
            for i in range(start_index, len(gen_strings)):
                await interaction.followup.send(f"{gen_strings[i]}", ephemeral=True)

        else:
        # handle case where player has no colonies, e.g., send a message
            await interaction.response.send_message("You have no colonies.\nIf you haven't joined the game yet, please run command /join")
            return
        
        #player_instance.view_torbs(player_instance.colonies[1])
    except Exception as e:
        error_type = type(e).__name__
        error_traceback = traceback.format_exc()
        print(error_traceback)  # or save it to a log file
        await interaction.response.send_message(f"Error ({error_type}): {e}")
    return

@client.event
async def on_ready():
    await tree.sync()
    await tree.sync(guild=discord.Object(id=guildID))
    print(f"Bot {client.user.name} is ready") 
    return





token = input("Token: ")
client.run(token)

