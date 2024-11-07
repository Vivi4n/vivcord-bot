from discord.ext import commands
import discord
from utils.database import Database
from utils.time_parser import parse_time, format_duration
from datetime import datetime, timedelta
import asyncio

class Mute(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database('data/user_logs.json')
        self.temp_mutes = {}
        self.load_active_mutes()  # This calls the method we're about to define

    def load_active_mutes(self):  # Add this method right here
        """Load active temporary mutes from the database"""
        try:
            for user_id, user_data in self.db.data.items():
                for mute in user_data.get('mutes', []):
                    if mute.get('expires_at'):
                        expires_at = datetime.fromisoformat(mute['expires_at'])
                        if expires_at > datetime.utcnow():
                            self.temp_mutes[user_id] = {
                                'guild_id': mute['guild_id'],
                                'expires_at': expires_at
                            }
        except Exception as e:
            print(f"Error loading active mutes: {e}")

    async def log_to_modchannel(self, guild, embed):
        """Send log message to mod-logs channel"""
        mod_channel = discord.utils.get(guild.channels, name='mod-logs')
        if mod_channel:
            await mod_channel.send(embed=embed)
    
    async def check_temp_mutes(self):
        """Check and unmute users whose temporary mute has expired"""
        await self.bot.wait_until_ready()  # Make sure bot is ready before starting loop
        
        while not self.bot.is_closed():
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
                                    
                                    # Create log embed
                                    embed = discord.Embed(
                                        title="Member Unmuted (Auto)",
                                        color=discord.Color.green(),
                                        timestamp=current_time
                                    )
                                    embed.add_field(name="Member", value=f"{member.mention} ({member.name})", inline=False)
                                    embed.add_field(name="Reason", value="Temporary mute expired", inline=False)
                                    embed.set_footer(text=f"User ID: {member.id}")
                                    
                                    # Send to mod-logs
                                    await self.log_to_modchannel(guild, embed)
                                    
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
                
            except Exception as e:
                print(f"Error in check_temp_mutes: {e}")
            
            await asyncio.sleep(60)  # Check every minute
    
    async def cog_load(self):
        """This is called when the cog is loaded"""
        self.temp_mute_task = self.bot.loop.create_task(self.check_temp_mutes())
    
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def mute(self, ctx, member: discord.Member, duration: str = None, *, reason=None):
        """Mute a member temporarily or permanently
        Usage: !mute @user [duration] [reason]
        Duration format: 30m, 24h, 7d (optional, if not provided, mute is permanent)
        """
        if member.top_role >= ctx.author.top_role:
            await ctx.send("You cannot mute a member with higher or equal role!")
            return
            
        if duration and not reason:
            reason = duration
            duration = None
        
        duration_seconds = parse_time(duration) if duration else None
        
        # Calculate expiry time if duration is provided
        expires_at = None
        if duration_seconds:
            expires_at = datetime.utcnow() + timedelta(seconds=duration_seconds)
        
        muted_role = await self.ensure_muted_role(ctx.guild)
        await member.add_roles(muted_role, reason=reason)
        
        # Create embed for mod-logs
        embed = discord.Embed(
            title="Member Muted",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Member", value=f"{member.mention} ({member.name})", inline=False)
        embed.add_field(name="Moderator", value=f"{ctx.author.mention} ({ctx.author.name})", inline=False)
        embed.add_field(name="Duration", value=format_duration(duration_seconds) if duration_seconds else "Permanent", inline=False)
        embed.add_field(name="Reason", value=reason or "No reason provided", inline=False)
        embed.set_footer(text=f"User ID: {member.id}")
        
        # Send to mod-logs
        await self.log_to_modchannel(ctx.guild, embed)
        
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
        await ctx.send(f"{member.mention} has been muted{duration_text}. Reason: {reason or 'No reason provided'}")

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def unmute(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Unmute a member
        Usage: !unmute @user [reason]
        """
        if member.top_role >= ctx.author.top_role:
            await ctx.send("You cannot unmute a member with higher or equal role!")
            return
            
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        
        if not muted_role:
            await ctx.send("No Muted role found!")
            return
            
        if muted_role not in member.roles:
            await ctx.send(f"{member.mention} is not muted!")
            return
            
        await member.remove_roles(muted_role, reason=reason)
        
        # Create embed for mod-logs
        embed = discord.Embed(
            title="Member Unmuted",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Member", value=f"{member.mention} ({member.name})", inline=False)
        embed.add_field(name="Moderator", value=f"{ctx.author.mention} ({ctx.author.name})", inline=False)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.set_footer(text=f"User ID: {member.id}")
        
        # Send to mod-logs
        await self.log_to_modchannel(ctx.guild, embed)
        
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
        
        await ctx.send(f"{member.mention} has been unmuted. Reason: {reason}")

async def setup(bot):
    await bot.add_cog(Mute(bot))