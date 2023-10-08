from email import message
import discord
from discord import app_commands

guildID = input("GuildID: ")

intents = discord.Intents.default()

intents.messages = True
intents.message_content = True
client = discord.Client(intents = intents)
tree = app_commands.CommandTree(client)

@tree.command(guild=discord.Object(id=guildID))
async def command1(interaction: discord.Interaction):
    await interaction.response.send_message("Test message")
    
@client.event
async def on_ready():
    print(f"Bot {client.user.name} is ready") 

@app_commands.command()
async def slash(interaction: discord.Interaction, number: int, string: str):
    await interaction.response.send_message(f'{number=} {string=}', ephemeral=True)

# Can also specify a guild here, but this example chooses not to.
tree.add_command(slash)

token = input("Token: ")
client.run(token)