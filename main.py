import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio
import logging
import traceback
from datetime import datetime

# Set up logging with more verbose output
logging.basicConfig(
    level=logging.DEBUG,  # Change to DEBUG level
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
        # Set up intents
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        intents.guilds = True
        
        # Initialize the bot
        super().__init__(
            command_prefix='!',
            intents=intents,
            case_insensitive=True,
            help_command=commands.DefaultHelpCommand(
                no_category="Other"
            )
        )
        
        # Store startup time
        self.start_time = datetime.utcnow()
        self.logger = logging.getLogger('AdminBot')
    
    async def setup_hook(self):
        """Setup hook that gets called before the bot starts"""
        try:
            self.logger.debug("Starting setup hook...")
            
            # Create necessary directories
            directories = ['data', 'logs']
            for directory in directories:
                os.makedirs(directory, exist_ok=True)
                self.logger.debug(f"Created/verified directory: {directory}")
            
            # Ensure utils and cogs directories exist
            os.makedirs('utils', exist_ok=True)
            os.makedirs('cogs', exist_ok=True)
            self.logger.debug("Created/verified utils and cogs directories")
            
            # Create __init__.py files if they don't exist
            open('utils/__init__.py', 'a').close()
            open('cogs/__init__.py', 'a').close()
            self.logger.debug("Created/verified __init__.py files")
            
            # Load all cogs
            await self.load_cogs()
            
        except Exception as e:
            self.logger.error(f"Error in setup: {str(e)}")
            self.logger.error(traceback.format_exc())
    
    async def load_cogs(self):
        """Load all cogs from the cogs directory"""
        self.logger.info("Loading cogs...")
        
        # List of cogs to load
        cogs = [
            'moderation',
            'mute',
            'warnings',
            'error_handler',
            'logger'
        ]
        
        for cog in cogs:
            try:
                self.logger.debug(f'Starting to load cog: {cog}')
                self.logger.debug(f'Looking for cog at: cogs.{cog}')
                await self.load_extension(f'cogs.{cog}')
                self.logger.info(f'Successfully loaded cog: {cog}')
            except Exception as e:
                self.logger.error(f'Failed to load cog {cog}: {str(e)}')
                self.logger.error(traceback.format_exc())
    
    async def on_ready(self):
        """Called when the bot is ready and connected to Discord"""
        self.logger.info(f'{self.user} has connected to Discord!')
        self.logger.info(f'Connected to {len(self.guilds)} guilds')
        
        # Set bot status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="for fat people"
            )
        )

async def main():
    try:
        # Get the token from environment variables
        token = os.getenv('DISCORD_TOKEN')
        if not token:
            raise ValueError("No Discord token found in .env file")
        
        # Create and run the bot
        bot = AdminBot()
        async with bot:
            await bot.start(token)
            
    except ValueError as e:
        logging.error(f"Configuration error: {str(e)}")
    except discord.LoginFailure:
        logging.error("Failed to login: Invalid Discord token")
    except Exception as e:
        logging.error(f"Fatal error: {str(e)}")
        logging.error(traceback.format_exc())

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot shutting down...")
    except Exception as e:
        logging.error(f"Fatal error: {str(e)}")
        logging.error(traceback.format_exc())