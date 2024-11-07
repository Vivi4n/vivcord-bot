import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio
import logging
from datetime import datetime

# Set up logging
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
        # Set up intents
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        intents.guilds = True
        
        # Initialize the bot
        super().__init__(
            command_prefix='!',
            intents=intents,
            case_insensitive=True,  # Commands will work regardless of case
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
            # Create necessary directories
            directories = ['data', 'logs']
            for directory in directories:
                os.makedirs(directory, exist_ok=True)
            
            # Ensure utils and cogs directories exist
            os.makedirs('utils', exist_ok=True)
            os.makedirs('cogs', exist_ok=True)
            
            # Create __init__.py files if they don't exist
            open('utils/__init__.py', 'a').close()
            open('cogs/__init__.py', 'a').close()
            
            # Load all cogs
            await self.load_cogs()
            
        except Exception as e:
            self.logger.error(f"Error in setup: {str(e)}")
    
    async def load_cogs(self):
        """Load all cogs from the cogs directory"""
        self.logger.info("Loading cogs...")
        
        # List of cogs to load
        cogs = [
            'moderation',
            'mute',
            'warnings',
            'error_handler'
        ]
        
        for cog in cogs:
            try:
                await self.load_extension(f'cogs.{cog}')
                self.logger.info(f'Successfully loaded cog: {cog}')
            except Exception as e:
                self.logger.error(f'Failed to load cog {cog}: {str(e)}')
    
    async def on_ready(self):
        """Called when the bot is ready and connected to Discord"""
        self.logger.info(f'{self.user} has connected to Discord!')
        self.logger.info(f'Connected to {len(self.guilds)} guilds')
        
        # Set bot status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="for rule breakers"
            )
        )
    
    async def on_guild_join(self, guild):
        """Called when the bot joins a new guild"""
        self.logger.info(f'Joined new guild: {guild.name} (id: {guild.id})')
        
        # Initialize moderation logs channel
        try:
            if not discord.utils.get(guild.channels, name='mod-logs'):
                await guild.create_text_channel('mod-logs')
                self.logger.info(f'Created mod-logs channel in {guild.name}')
        except discord.Forbidden:
            self.logger.warning(f'Could not create mod-logs channel in {guild.name}: Missing permissions')
    
    async def on_guild_remove(self, guild):
        """Called when the bot is removed from a guild"""
        self.logger.info(f'Removed from guild: {guild.name} (id: {guild.id})')
    
    async def on_command_error(self, ctx, error):
        """Global error handler for command errors"""
        if isinstance(error, commands.CommandNotFound):
            await ctx.send("Command not found. Use !help to see available commands.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permission to use this command!")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing required argument: {error.param.name}")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Bad argument provided. Please check the command usage with !help")
        else:
            # Log unexpected errors
            self.logger.error(f'Unexpected error in {ctx.command}: {str(error)}')
            await ctx.send("An unexpected error occurred. Please try again later.")

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

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot shutting down...")
    except Exception as e:
        logging.error(f"Fatal error: {str(e)}")