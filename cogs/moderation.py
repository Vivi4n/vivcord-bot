from discord.ext import commands
import discord
from utils.database import Database
from utils.time_parser import parse_time
from datetime import datetime, timedelta
import asyncio

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database('data/user_logs.json')
        self.temp_bans = {}
        self.load_active_bans()
        # Remove the direct call to check_temp_bans
    
    async def cog_load(self):
        """This is called when the cog is loaded"""
        # Start the background task properly
        self.temp_ban_task = self.bot.loop.create_task(self.check_temp_bans())
    
    async def cog_unload(self):
        """This is called when the cog is unloaded"""
        # Make sure we clean up the background task
        if hasattr(self, 'temp_ban_task'):
            self.temp_ban_task.cancel()
    
    def load_active_bans(self):
        """Load active temporary bans from the database"""
        for user_id, user_data in self.db.data.items():
            for ban in user_data.get('bans', []):
                if ban.get('expires_at'):
                    expires_at = datetime.fromisoformat(ban['expires_at'])
                    if expires_at > datetime.utcnow():
                        self.temp_bans[user_id] = {
                            'guild_id': ban['guild_id'],
                            'expires_at': expires_at
                        }
    
    async def check_temp_bans(self):
        """Check and unban users whose temporary ban has expired"""
        while True:
            try:
                current_time = datetime.utcnow()
                to_remove = []
                
                for user_id, ban_data in self.temp_bans.items():
                    if current_time >= ban_data['expires_at']:
                        guild = self.bot.get_guild(ban_data['guild_id'])
                        if guild:
                            try:
                                # Get the ban entry
                                ban_entry = await guild.fetch_ban(discord.Object(id=int(user_id)))
                                if ban_entry:
                                    await guild.unban(ban_entry.user, reason="Temporary ban expired")
                                    
                                    # Log the automatic unban
                                    self.db.log_action(
                                        int(user_id),
                                        "unban",
                                        {
                                            "reason": "Temporary ban expired",
                                            "moderator": self.bot.user.id,
                                            "moderator_name": str(self.bot.user),
                                            "timestamp": str(current_time)
                                        }
                                    )
                            except discord.NotFound:
                                pass  # User was already unbanned
                        to_remove.append(user_id)
                
                # Remove expired bans
                for user_id in to_remove:
                    del self.temp_bans[user_id]
                
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                print(f"Error in check_temp_bans: {e}")
                await asyncio.sleep(60)  # Still sleep on error

async def setup(bot):
    """Proper setup function that doesn't call the background task directly"""
    await bot.add_cog(Moderation(bot))