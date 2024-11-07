from discord.ext import commands
import discord
from utils.database import Database
from utils.time_parser import parse_time, format_duration
from datetime import datetime, timedelta
import asyncio

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database('data/user_logs.json')
        self.temp_bans = {}
        self.load_active_bans()

    async def log_to_modchannel(self, guild, embed):
        """Send log message to mod-logs channel"""
        mod_channel = discord.utils.get(guild.channels, name='mod-logs')
        if mod_channel:
            await mod_channel.send(embed=embed)

    async def check_temp_bans(self):
        """Check and unban users whose temporary ban has expired"""
        await self.bot.wait_until_ready()
        
        while not self.bot.is_closed():
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
                                    
                                    # Create log embed
                                    embed = discord.Embed(
                                        title="Member Unbanned (Auto)",
                                        color=discord.Color.green(),
                                        timestamp=current_time
                                    )
                                    embed.add_field(name="Member", value=f"{ban_entry.user} ({ban_entry.user.name})", inline=False)
                                    embed.add_field(name="Reason", value="Temporary ban expired", inline=False)
                                    embed.set_footer(text=f"User ID: {ban_entry.user.id}")
                                    
                                    # Send to mod-logs
                                    await self.log_to_modchannel(guild, embed)
                                    
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
                                    
                                    to_remove.append(user_id)
                            except discord.NotFound:
                                pass  # User was already unbanned
                
                # Remove expired bans
                for user_id in to_remove:
                    del self.temp_bans[user_id]
                
            except Exception as e:
                print(f"Error in check_temp_bans: {e}")
            
            await asyncio.sleep(60)  # Check every minute

    async def cog_load(self):
        """This is called when the cog is loaded"""
        self.temp_ban_task = self.bot.loop.create_task(self.check_temp_bans())

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, duration: str = None, *, reason=None):
        """Ban a member temporarily or permanently
        Usage: !ban @user [duration] [reason]
        Duration format: 30m, 24h, 7d (optional, if not provided, ban is permanent)
        """
        if member.top_role >= ctx.author.top_role:
            await ctx.send("You cannot ban a member with higher or equal role!")
            return

        if duration and not reason:
            reason = duration
            duration = None
        
        duration_seconds = parse_time(duration) if duration else None
        
        # Calculate expiry time if duration is provided
        expires_at = None
        if duration_seconds:
            expires_at = datetime.utcnow() + timedelta(seconds=duration_seconds)
        
        await member.ban(reason=reason)
        
        # Create embed for mod-logs
        embed = discord.Embed(
            title="Member Banned",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Member", value=f"{member.mention} ({member.name})", inline=False)
        embed.add_field(name="Moderator", value=f"{ctx.author.mention} ({ctx.author.name})", inline=False)
        embed.add_field(name="Duration", value=format_duration(duration_seconds) if duration_seconds else "Permanent", inline=False)
        embed.add_field(name="Reason", value=reason or "No reason provided", inline=False)
        embed.set_footer(text=f"User ID: {member.id}")
        
        # Send to mod-logs
        await self.log_to_modchannel(ctx.guild, embed)
        
        # Log the ban
        ban_data = {
            "reason": reason,
            "moderator": ctx.author.id,
            "moderator_name": str(ctx.author),
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
        await ctx.send(f"{member.mention} has been banned{duration_text}. Reason: {reason or 'No reason provided'}")

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, *, member):
        """Unban a member"""
        banned_users = [entry async for entry in ctx.guild.bans()]
        member_name, member_discriminator = member.split('#')
        
        for ban_entry in banned_users:
            user = ban_entry.user
            if (user.name, user.discriminator) == (member_name, member_discriminator):
                await ctx.guild.unban(user)
                
                # Create embed for mod-logs
                embed = discord.Embed(
                    title="Member Unbanned",
                    color=discord.Color.green(),
                    timestamp=datetime.utcnow()
                )
                embed.add_field(name="Member", value=f"{user} ({user.name})", inline=False)
                embed.add_field(name="Moderator", value=f"{ctx.author.mention} ({ctx.author.name})", inline=False)
                embed.add_field(name="Reason", value="Manual unban by moderator", inline=False)
                embed.set_footer(text=f"User ID: {user.id}")
                
                # Send to mod-logs
                await self.log_to_modchannel(ctx.guild, embed)
                
                # Remove from temp_bans if it was a temporary ban
                if str(user.id) in self.temp_bans:
                    del self.temp_bans[str(user.id)]
                
                # Log the manual unban
                self.db.log_action(
                    user.id,
                    "unban",
                    {
                        "reason": "Manual unban by moderator",
                        "moderator": ctx.author.id,
                        "moderator_name": str(ctx.author),
                        "timestamp": str(datetime.utcnow())
                    }
                )
                
                await ctx.send(f"{user.mention} has been unbanned.")
                return

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        """Kick a member"""
        if member.top_role >= ctx.author.top_role:
            await ctx.send("You cannot kick a member with higher or equal role!")
            return

        await member.kick(reason=reason)
        
        # Create embed for mod-logs
        embed = discord.Embed(
            title="Member Kicked",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Member", value=f"{member.mention} ({member.name})", inline=False)
        embed.add_field(name="Moderator", value=f"{ctx.author.mention} ({ctx.author.name})", inline=False)
        embed.add_field(name="Reason", value=reason or "No reason provided", inline=False)
        embed.set_footer(text=f"User ID: {member.id}")
        
        # Send to mod-logs
        await self.log_to_modchannel(ctx.guild, embed)
        
        self.db.log_action(
            member.id,
            "kick",
            {
                "reason": reason,
                "moderator": ctx.author.id,
                "moderator_name": str(ctx.author),
                "timestamp": str(datetime.utcnow()),
                "guild_id": ctx.guild.id
            }
        )
        
        await ctx.send(f"{member.mention} has been kicked. Reason: {reason or 'No reason provided'}")

async def setup(bot):
    await bot.add_cog(Moderation(bot))