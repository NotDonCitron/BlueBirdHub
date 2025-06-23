import discord
from discord import app_commands
import os
from dotenv import load_dotenv
from claude_client import send_to_claude

# --- Configuration ---
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = os.getenv("DISCORD_GUILD_ID") # Your Server's ID

if not DISCORD_TOKEN or not GUILD_ID:
    print("Error: DISCORD_BOT_TOKEN and DISCORD_GUILD_ID must be set in a .env file.")
    exit()

# --- Bot Setup ---
class ClaudeBot(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)

intents = discord.Intents.default()
client = ClaudeBot(intents=intents)

# --- Events ---
@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')

# --- Commands ---
@client.tree.command(name="claude", description="Send a prompt to Claude.")
@app_commands.describe(prompt="The prompt to send to Claude.")
async def claude_command(interaction: discord.Interaction, prompt: str):
    await interaction.response.defer() # Acknowledge the command immediately
    
    # Send the prompt to Claude and get the response
    response = send_to_claude(prompt)
    
    # Send the response back to the channel
    # Discord has a 2000 character limit per message
    if len(response) > 2000:
        # Split the response into chunks
        for i in range(0, len(response), 2000):
            await interaction.followup.send(response[i:i+2000])
    else:
        await interaction.followup.send(response)

# --- Run Bot ---
if __name__ == "__main__":
    client.run(DISCORD_TOKEN) 