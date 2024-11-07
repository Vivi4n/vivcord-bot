# main.py
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AdminBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
        
    async def setup_hook(self):
        # Load all cogs
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                await self.load_extension(f'cogs.{filename[:-3]}')
                print(f'Loaded {filename[:-3]}')

    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')
        
if __name__ == '__main__':
    bot = AdminBot()
    bot.run(os.getenv('DISCORD_TOKEN'))