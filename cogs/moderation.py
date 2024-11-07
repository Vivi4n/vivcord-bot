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
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Start the temporary ban checker when the bot is ready"""
        self.bot.loop.create_task(self.check_temp_bans())
    
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, duration: str = None, *, reason=None):
        """Ban a member temporarily or permanently
        Usage: !ban @user [duration] [reason]
        Duration format: 30m, 24h, 7d (optional, if not provided, ban is permanent)
        """
        if duration and not reason:
            # If only two arguments provided, treat the second as reason
            reason = duration
            duration = None
        
        duration_seconds = parse_time(duration) if duration else None
        
        # Calculate expiry time if duration is provided
        expires_at = None
        if duration_seconds:
            expires_at = datetime.utcnow() + timedelta(seconds=duration_seconds)
        
        await member.ban(reason=reason)
        
        # Log the ban
        ban_data = {
            "reason": reason,
            "moderator": ctx.author.id,
            "moderator_name": f"{ctx.author.name}#{ctx.author.discriminator}",
            "timestamp": str(datetime.utcnow()),
            "guild_id": ctx.guild.id
        }
        
        if expires_at:
            ban_data["expires_at"] = str(expires_at)
            self.temp_bans[str(member.id)] = {
                'guild_id': ctx.guild.id,
                'expires_at': expires_at
            }
        
        self.db.log_action(member.id, "ban", ban_data)
        
        # Send confirmation message
        duration_text = f" for {duration}" if duration else ""
        await ctx.send(f"{member.mention} has been banned{duration_text}. Reason: {reason}")