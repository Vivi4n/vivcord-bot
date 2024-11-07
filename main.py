import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio
import logging
from datetime import datetime
from utils.database import Database  # Add this import

# Set up logging with less verbose output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(filename='bot.log', encoding='utf-8', mode='a'),
        logging.StreamHandler()
    ]
)

# Load environment variables
load_dotenv()

class AdminBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        intents.guilds = True
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            case_insensitive=True,
            help_command=commands.DefaultHelpCommand(
                no_category="Other"
            )
        )
        
        self.start_time = datetime.utcnow()
        self.logger = logging.getLogger('AdminBot')
        self.db = Database('data/user_logs.json')
    
    async def setup_hook(self):
        """Setup hook that gets called before the bot starts"""
        try:
            # Create necessary directories
            directories = ['data', 'logs', 'utils', 'cogs']
            for directory in directories:
                os.makedirs(directory, exist_ok=True)
            
            # Create __init__.py files if they don't exist
            open('utils/__init__.py', 'a').close()
            open('cogs/__init__.py', 'a').close()
            
            # Load all cogs
            await self.load_cogs()
            
            # Sync slash commands
            await self.tree.sync()
            
        except Exception as e:
            self.logger.error(f"Error in setup: {str(e)}")
    
    async def load_cogs(self):
        """Load all cogs from the cogs directory"""
        self.logger.info("Loading cogs...")
        
        cogs = [
            'moderation',
            'mute',
            'warnings',
            'error_handler',
            'stats',
            'anime_commands'
        ]
        
        for cog in cogs:
            try:
                await self.load_extension(f'cogs.{cog}')
                self.logger.info(f'Loaded: {cog}')
            except Exception as e:
                self.logger.error(f'Failed to load {cog}: {str(e)}')
    
    async def on_ready(self):
        """Called when the bot is ready and connected to Discord"""
        self.logger.info(f'{self.user} has connected to Discord!')
        self.logger.info(f'Connected to {len(self.guilds)} guilds')
        
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="you through ur walls"
            )
        )
    
    async def on_guild_join(self, guild):
        """Called when the bot joins a new guild"""
        self.logger.info(f'Joined new guild: {guild.name} (id: {guild.id})')
        
        try:
            if not discord.utils.get(guild.channels, name='mod-logs'):
                await guild.create_text_channel('mod-logs')
        except discord.Forbidden:
            self.logger.warning(f'Could not create mod-logs channel in {guild.name}')
    
    async def on_guild_remove(self, guild):
        """Called when the bot is removed from a guild"""
        self.logger.info(f'Removed from guild: {guild.name} (id: {guild.id})')

async def main():
    try:
        token = os.getenv('DISCORD_TOKEN')
        if not token:
            raise ValueError("No Discord token found in .env file")
        
        bot = AdminBot()
        async with bot:
            await bot.start(token)
            
    except ValueError as e:
        logging.error(f"Configuration error: {str(e)}")
    except discord.LoginFailure:
        logging.error("Failed to login: Invalid Discord token")
    except Exception as e:
        logging.error(f"Fatal error: {str(e)}")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot shutting down...")
    except Exception as e:
        logging.error(f"Fatal error: {str(e)}")