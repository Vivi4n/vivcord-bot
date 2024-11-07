from discord.ext import commands
import discord
from utils.database import Database
from utils.time_parser import parse_time
from datetime import datetime, timedelta
import asyncio

class Mute(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database('data/user_logs.json')
        self.temp_mutes = {}
        self.load_active_mutes()
    
    def load_active_mutes(self):
        """Load active temporary mutes from the database"""
        for user_id, user_data in self.db.data.items():
            for mute in user_data.get('mutes', []):
                if mute.get('expires_at'):
                    expires_at = datetime.fromisoformat(mute['expires_at'])
                    if expires_at > datetime.utcnow():
                        self.temp_mutes[user_id] = {
                            'guild_id': mute['guild_id'],
                            'expires_at': expires_at
                        }
    
    async def check_temp_mutes(self):
        """Check and unmute users whose temporary mute has expired"""
        while True:
            try:
                current_time = datetime.utcnow()
                to_remove = []
                
                for user_id, mute_data in self.temp_mutes.items():
                    if current_time >= mute_data['expires_at']:
                        guild = self.bot.get_guild(mute_data['guild_id'])
                        if guild:
                            member = guild.get_member(int(user_id))
                            if member:
                                muted_role = discord.utils.get(guild.roles, name="Muted")
                                if muted_role and muted_role in member.roles:
                                    await member.remove_roles(muted_role, reason="Temporary mute expired")
                                    
                                    # Log the automatic unmute
                                    self.db.log_action(
                                        int(user_id),
                                        "unmute",
                                        {
                                            "reason": "Temporary mute expired",
                                            "moderator": self.bot.user.id,
                                            "moderator_name": str(self.bot.user),
                                            "timestamp": str(current_time)
                                        }
                                    )
                    to_remove.append(user_id)
                
                # Remove expired mutes
                for user_id in to_remove:
                    del self.temp_mutes[user_id]
                
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                print(f"Error in check_temp_mutes: {e}")
                await asyncio.sleep(60)
    
    async def cog_load(self):
        """This is called when the cog is loaded"""
        # Start the background task properly
        self.temp_mute_task = self.bot.loop.create_task(self.check_temp_mutes())
    
    async def cog_unload(self):
        """This is called when the cog is unloaded"""
        # Make sure we clean up the background task
        if hasattr(self, 'temp_mute_task'):
            self.temp_mute_task.cancel()
    
    async def ensure_muted_role(self, guild):
        """Ensure the Muted role exists and has proper permissions"""
        muted_role = discord.utils.get(guild.roles, name="Muted")
        if not muted_role:
            muted_role = await guild.create_role(name="Muted")
            for channel in guild.channels:
                await channel.set_permissions(muted_role, speak=False, send_messages=False)
        return muted_role
    
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def mute(self, ctx, member: discord.Member, duration: str = None, *, reason=None):
        """Mute a member temporarily or permanently
        Usage: !mute @user [duration] [reason]
        Duration format: 30m, 24h, 7d (optional, if not provided, mute is permanent)
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
        
        muted_role = await self.ensure_muted_role(ctx.guild)
        await member.add_roles(muted_role, reason=reason)
        
        # Log the mute
        mute_data = {
            "reason": reason,
            "moderator": ctx.author.id,
            "moderator_name": str(ctx.author),
            "timestamp": str(datetime.utcnow()),
            "guild_id": ctx.guild.id
        }
        
        if expires_at:
            mute_data["expires_at"] = str(expires_at)
            self.temp_mutes[str(member.id)] = {
                'guild_id': ctx.guild.id,
                'expires_at': expires_at
            }
        
        self.db.log_action(member.id, "mute", mute_data)
        
        # Send confirmation message
        duration_text = f" for {duration}" if duration else ""
        await ctx.send(f"{member.mention} has been muted{duration_text}. Reason: {reason}")

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def unmute(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Unmute a member
        Usage: !unmute @user [reason]
        """
        # Get the Muted role
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        
        if not muted_role:
            await ctx.send("No Muted role found!")
            return
            
        if muted_role not in member.roles:
            await ctx.send(f"{member.mention} is not muted!")
            return
            
        # Remove the Muted role
        await member.remove_roles(muted_role, reason=reason)
        
        # Remove from temp_mutes if it was a temporary mute
        if str(member.id) in self.temp_mutes:
            del self.temp_mutes[str(member.id)]
        
        # Log the unmute
        self.db.log_action(
            member.id,
            "unmute",
            {
                "reason": reason,
                "moderator": ctx.author.id,
                "moderator_name": str(ctx.author),
                "timestamp": str(datetime.utcnow()),
                "guild_id": ctx.guild.id
            }
        )
        
        # Send confirmation message
        await ctx.send(f"{member.mention} has been unmuted. Reason: {reason}")

async def setup(bot):
    await bot.add_cog(Mute(bot))