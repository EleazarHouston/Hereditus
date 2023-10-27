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
async def command1(interaction: discord.Interaction):
    await interaction.response.send_message("Everyone can see this!")
    await interaction.followup.send("Only you can see this!",ephemeral=True)
    return

@tree.command(guild=discord.Object(id=guildID))
async def new_game(interaction: discord.Interaction):
    from simulator import Simulator
    a = Simulator(Simulator._next_SID)
    a.new_evolution_engine()
    await interaction.response.send_message(f"New game available: Game ID: {a.SID}\nRun /join_game to join the game, then wait for the game to start.")
    return

@tree.command(guild=discord.Object(id=guildID))
async def start_game(interaction: discord.Interaction, sid: int, num_torbs: int):
    from simulator import Simulator
    try:
        Simulator._instances[sid].init_all_colonies(num_torbs)
    except KeyError:
        await interaction.response.send_message(f"Command Invalid: Invalid Game ID")
        return
    await interaction.response.send_message("Colonies initialzed.\nGame has started\nPlayer commands available:\n/colony_info\n/breed")
    return

@tree.command(guild=discord.Object(id=guildID))
async def join_game(interaction: discord.Interaction, game_id: int, colony_name: str):
    if len(colony_name) > 16:
        await interaction.response.send_message("Invalid Colony Name: Name must be 16 characters or fewer")
        return
    elif not colony_name.isalnum():
        await interaction.response.send_message("Invalid Colony Name: Name must have only letters and numbers")
        return
    
    from simulator import Simulator
    
    try:
        if interaction.user.id in Player._instances:
            await interaction.response.send_message("Command Invalid: You have already joined this game.")
            return
        else:
            a = Player(interaction.user.id)
            
        Simulator._instances[game_id].new_colony(colony_name, 0, interaction.user.id)
        
        await interaction.response.send_message("Colony generated! Welcome to the game!")
    except KeyError:
        await interaction.response.send_message(f"Command Invalid: Invalid Game ID")
    return

@tree.command(guild=discord.Object(id=guildID))
async def breed(interaction: discord.Interaction, breeding_pairs: str):
    player_instance = Player._instances[interaction.user.id]
    player_instance.call_colony_reproduction(player_instance.colonies[0], breeding_pairs)
    await interaction.response.send_message(f"Torbs bred. Run /colony_info to see torbs")
    return

@tree.command(guild=discord.Object(id=guildID))
async def colony_info(interaction: discord.Interaction):
    print("Trying dsicord command colony_info")
    try:
        player_instance = Player._instances[interaction.user.id]
        print(f"{interaction.user.id}")
        print(f"{player_instance.colony_count}")
        from simulator import Simulator
        if Simulator._instances[0].started == False:
            await interaction.response.send_message("The game hasn't started yet.\nPlease wait for an admin to start the game.")
            return
        if player_instance.colonies:
            first_colony_key = list(player_instance.colonies.keys())[0]
            print(first_colony_key)
            gen_strings = []
            for i in range(0, player_instance.colonies[0].generations+1):
                gen_strings.append(player_instance.view_torbs(player_instance.colonies[first_colony_key].CID, i))
            #torb_string = player_instance.view_torbs(player_instance.colonies[first_colony_key])
            for i, gen_string in enumerate(gen_strings):
                if i == 0:
                    await interaction.response.send_message(f"{gen_strings[0]}")
                else:
                    await interaction.followup.send(f"{gen_strings[i]}")
        else:
        # handle case where player has no colonies, e.g., send a message
            await interaction.response.send_message("You have no colonies.\nIf you haven't joined the game yet, please run command /join_game")
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

@app_commands.command()
async def slash(interaction: discord.Interaction, number: int, string: str):
    await interaction.response.send_message(f'{number=} {string=}', ephemeral=True)
    


# Can also specify a guild here, but this example chooses not to.
tree.add_command(slash)

token = input("Token: ")
client.run(token)

