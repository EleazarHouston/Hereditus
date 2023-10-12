from email import message
import discord
from discord import app_commands
import torb
import ast

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
    
@tree.command(guild=discord.Object(id=guildID))
async def generate(interaction: discord.Interaction, colony_id: int):
    
    if not isinstance(colony_id, int):
        await interaction.response.send_message("Please enter an integer for colony_id")
        return

    if not colony_id in torb.Colony._instances:
        torb.Colony(colony_id, f"C{colony_id}", 0)
        
    
    torb.Colony._instances[colony_id].init_gen_zero(8)
    #torb.C0.init_gen_zero(8)
    out = torb.Colony._instances[colony_id].out_torbs()
    await interaction.response.send_message(f"{out}")
    #await interaction.followup.send("Only you can see this!",ephemeral=True)

@tree.command(guild=discord.Object(id=guildID))
async def reset_colony(interaction: discord.Interaction, colony_id: int):
    if not isinstance(colony_id, int):
        await interaction.response.send_message("Please enter an integer for colony_id")
        return
    if not colony_id in torb.Colony._instances:
        await interaction.response.send_message(f"Error: Colony not found")
        return
    #torb.Colony._instances[colony_id]
    C99 = torb.Colony(colony_id, f"C{colony_id}", 0)
    torb.Colony._instances[colony_id].init_gen_zero(8)
    out = torb.Colony._instances[colony_id].out_torbs()
    await interaction.response.send_message(f"{out}")

@tree.command(guild=discord.Object(id=guildID))
async def breed(interaction: discord.Interaction, colony_id: int, pairs: str):
    if not isinstance(colony_id, int):
        await interaction.response.send_message("Please enter an integer for colony_id")
        return
    if not colony_id in torb.Colony._instances:
        await interaction.response.send_message(f"Error: Colony not found")
        return
    pairs = ast.literal_eval(pairs)
    if isinstance(pairs, list) and all(isinstance(sublist, list) for sublist in pairs):
        torb.Colony._instances[colony_id].colony_reproduction(pairs)
        out = torb.Colony._instances[colony_id].out_torbs()
        await interaction.response.send_message(f"{out}")
    else:
        await interaction.response.send_message(f"Error: Incorrectly formatted breeding pairs, use format [[0, 1], [2, 3]] to breed Torb 0 and 1 together and Torb 2 and 3 together")

@client.event
async def on_ready():
    await tree.sync()
    await tree.sync(guild=discord.Object(id=guildID))
    print(f"Bot {client.user.name} is ready") 

@app_commands.command()
async def slash(interaction: discord.Interaction, number: int, string: str):
    await interaction.response.send_message(f'{number=} {string=}', ephemeral=True)
    


# Can also specify a guild here, but this example chooses not to.
tree.add_command(slash)

token = input("Token: ")
client.run(token)

