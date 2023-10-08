import discord
from discord import app_commands


intents = discord.Intents.default()

intents.messages = True
intents.message_content = True
client = discord.Client(intents = intents)
tree = app_commands.CommandTree(client)

@tree.command(name = "test", description = "Test command")
async def command1(interaction):
    await interaction.response.send_message("Test message")