import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio
import logging
from datetime import datetime
from utils.database import Database

# Set logging to DEBUG level to see more information
logging.basicConfig(
    level=logging.DEBUG,  # Changed from INFO to DEBUG
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(filename='bot.log', encoding='utf-8', mode='a'),
        logging.StreamHandler()
    ]
)

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
        try:
            # Log the startup process
            self.logger.debug("Starting setup_hook")
            
            directories = ['data', 'logs', 'utils', 'cogs']
            for directory in directories:
                os.makedirs(directory, exist_ok=True)
                self.logger.debug(f"Ensured directory exists: {directory}")
            
            open('utils/__init__.py', 'a').close()
            open('cogs/__init__.py', 'a').close()
            
            await self.load_cogs()
            
            try:
                self.logger.info("Starting slash command sync...")
                self.logger.debug("Syncing global commands...")
                await self.tree.sync()
                self.logger.info("Global slash commands synced successfully")
                
                for guild in self.guilds:
                    try:
                        self.logger.debug(f"Syncing commands to guild: {guild.name}")
                        await self.tree.sync(guild=guild)
                        self.logger.info(f"Slash commands synced to guild: {guild.name}")
                    except Exception as e:
                        self.logger.error(f"Failed to sync commands to {guild.name}: {e}")
                        
            except Exception as e:
                self.logger.error(f"Failed to sync slash commands: {e}")
            
        except Exception as e:
            self.logger.error(f"Error in setup: {str(e)}")
    
    async def load_cogs(self):
        self.logger.debug("Starting to load cogs...")
        
        cogs = [
            'moderation',
            'mute',
            'warnings',
            'error_handler',
            'stats',
            'anime_commands',
            'custom_commands'
        ]
        
        for cog in cogs:
            try:
                self.logger.debug(f"Attempting to load cog: {cog}")
                await self.load_extension(f'cogs.{cog}')
                self.logger.info(f'Loaded: {cog}')
            except Exception as e:
                self.logger.error(f'Failed to load {cog}: {str(e)}')

    @commands.command()
    @commands.is_owner()
    async def sync(self, ctx, scope: str = "global"):
        self.logger.debug(f"Sync command received from {ctx.author} with scope: {scope}")
        try:
            await ctx.send("Starting sync process...")
            
            if scope == "guild":
                self.logger.debug(f"Syncing to guild: {ctx.guild.name}")
                synced = await self.tree.sync(guild=ctx.guild)
                await ctx.send(
                    f"Successfully synced {len(synced)} commands to the current guild."
                )
                self.logger.info(
                    f"Synced {len(synced)} commands to guild {ctx.guild.name}"
                )
                
            else:
                self.logger.debug("Syncing globally")
                synced = await self.tree.sync()
                await ctx.send(
                    f"Successfully synced {len(synced)} commands globally."
                )
                self.logger.info(f"Synced {len(synced)} commands globally")
                
        except Exception as e:
            self.logger.error(f"Sync error: {str(e)}")
            await ctx.send(f"Failed to sync commands: {str(e)}")

    @commands.command()
    @commands.is_owner()
    async def reload(self, ctx, cog: str):
        self.logger.debug(f"Reload command received from {ctx.author} for cog: {cog}")
        try:
            await ctx.send(f"Attempting to reload {cog}...")
            await self.reload_extension(f'cogs.{cog}')
            await ctx.send(f"Successfully reloaded {cog}")
            self.logger.info(f"Reloaded cog: {cog}")
            
            # Also sync commands after reload
            self.logger.debug("Syncing commands after reload")
            await self.tree.sync()
            await ctx.send("Synced commands after reload")
            
        except Exception as e:
            self.logger.error(f"Failed to reload {cog}: {str(e)}")
            await ctx.send(f"Failed to reload {cog}: {str(e)}")
    
    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info(f'{self.user} has connected to Discord!')
        self.logger.info(f'Connected to {len(self.guilds)} guilds')
        
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="you through ur walls"
            )
        )
    
    # Add message content logging to debug command detection
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
            
        self.logger.debug(f"Message received: {message.content}")
        await self.process_commands(message)