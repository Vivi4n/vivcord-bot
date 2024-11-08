import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio
import logging
from datetime import datetime
from utils.database import Database

logging.basicConfig(
    level=logging.INFO,
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
            directories = ['data', 'logs', 'utils', 'cogs']
            for directory in directories:
                os.makedirs(directory, exist_ok=True)
            
            open('utils/__init__.py', 'a').close()
            open('cogs/__init__.py', 'a').close()
            
            await self.load_cogs()
            
            try:
                self.logger.info("Syncing slash commands...")
                await self.tree.sync()
                self.logger.info("Global slash commands synced successfully")
                
                for guild in self.guilds:
                    try:
                        await self.tree.sync(guild=guild)
                        self.logger.info(f"Slash commands synced to guild: {guild.name}")
                    except Exception as e:
                        self.logger.error(f"Failed to sync commands to {guild.name}: {e}")
                        
            except Exception as e:
                self.logger.error(f"Failed to sync slash commands: {e}")
            
        except Exception as e:
            self.logger.error(f"Error in setup: {str(e)}")
    
    async def load_cogs(self):
        self.logger.info("Loading cogs...")
        
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
                await self.load_extension(f'cogs.{cog}')
                self.logger.info(f'Loaded: {cog}')
            except Exception as e:
                self.logger.error(f'Failed to load {cog}: {str(e)}')

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def clearcommands(self, ctx):
        """Remove all slash commands"""
        try:
            await ctx.send("Clearing all slash commands...")
            self.tree.clear_commands(guild=ctx.guild)  # Clear for current guild only
            await self.tree.sync(guild=ctx.guild)
            await ctx.send("Cleared all slash commands for this server.")
        except Exception as e:
            await ctx.send(f"Error clearing commands: {str(e)}")
            self.logger.error(f"Error in clearcommands: {str(e)}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def reloadall(self, ctx):
        """Reload all cogs and sync commands"""
        try:
            await ctx.send("Reloading all cogs...")
            # Reload all cogs
            for cog in list(self.cogs):
                try:
                    await self.reload_extension(f'cogs.{cog.lower()}')
                    await ctx.send(f"Reloaded: {cog}")
                except Exception as e:
                    await ctx.send(f"Failed to reload {cog}: {str(e)}")
                    return

            # Sync commands for this guild
            await ctx.send("Syncing commands...")
            await self.tree.sync(guild=ctx.guild)
            await ctx.send("All cogs reloaded and commands synced!")
            
        except Exception as e:
            await ctx.send(f"Error reloading cogs: {str(e)}")
            self.logger.error(f"Error in reloadall: {str(e)}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def sync(self, ctx):
        """Sync slash commands for this server"""
        try:
            await ctx.send("Syncing commands...")
            synced = await self.tree.sync(guild=ctx.guild)
            await ctx.send(f"Successfully synced {len(synced)} commands to this server.")
            self.logger.info(f"Synced {len(synced)} commands to guild {ctx.guild.name}")
        except Exception as e:
            await ctx.send(f"Failed to sync commands: {str(e)}")
            self.logger.error(f"Sync error: {str(e)}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def reload(self, ctx, cog: str):
        """Reload a specific cog"""
        try:
            await self.reload_extension(f'cogs.{cog}')
            await ctx.send(f"Successfully reloaded {cog}")
            # Sync commands after reload
            await self.tree.sync(guild=ctx.guild)
            self.logger.info(f"Reloaded cog: {cog}")
        except Exception as e:
            await ctx.send(f"Failed to reload {cog}: {str(e)}")
            self.logger.error(f"Failed to reload {cog}: {str(e)}")
    
    async def on_ready(self):
        self.logger.info(f'{self.user} has connected to Discord!')
        self.logger.info(f'Connected to {len(self.guilds)} guilds')
        
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="you through ur walls"
            )
        )
    
    async def on_guild_join(self, guild):
        self.logger.info(f'Joined new guild: {guild.name} (id: {guild.id})')
        
        try:
            if not discord.utils.get(guild.channels, name='mod-logs'):
                await guild.create_text_channel('mod-logs')
            
            await self.tree.sync(guild=guild)
            self.logger.info(f"Synced slash commands to new guild: {guild.name}")
            
        except discord.Forbidden:
            self.logger.warning(f'Could not create mod-logs channel in {guild.name}')
    
    async def on_guild_remove(self, guild):
        self.logger.info(f'Removed from guild: {guild.name} (id: {guild.id})')

    @clearcommands.error
    @reloadall.error
    @sync.error
    @reload.error
    async def admin_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You need administrator permissions to use this command.")
        else:
            await ctx.send(f"An error occurred: {str(error)}")

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