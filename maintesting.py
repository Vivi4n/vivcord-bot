import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio
import logging
from datetime import datetime

# Basic logging setup
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('Bot')
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
            case_insensitive=True
        )
    
    async def setup_hook(self):
        logger.info("Bot is setting up...")
        try:
            await self.load_extension('cogs.anime_commands')
            logger.info("Loaded anime_commands cog")
            await self.tree.sync()
            logger.info("Synced commands")
        except Exception as e:
            logger.error(f"Setup error: {str(e)}")

    async def on_ready(self):
        logger.info(f'Bot {self.user} is ready!')

async def main():
    try:
        token = os.getenv('DISCORD_TOKEN')
        if not token:
            raise ValueError("No Discord token found in .env file")
        
        logger.info("Starting bot...")
        bot = AdminBot()
        async with bot:
            await bot.start(token)
            
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")