from discord.ext import commands
import discord
from utils.database import Database
from datetime import datetime

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database('data/user_logs.json')
    
    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        """Kick a member"""
        await member.kick(reason=reason)
        
        self.db.log_action(
            member.id,
            "kick",
            {
                "reason": reason,
                "moderator": ctx.author.id,
                "moderator_name": f"{ctx.author.name}#{ctx.author.discriminator}",
                "timestamp": str(datetime.utcnow())
            }
        )
        
        await ctx.send(f"{member.mention} has been kicked. Reason: {reason}")
    
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        """Ban a member"""
        await member.ban(reason=reason)
        
        self.db.log_action(
            member.id,
            "ban",
            {
                "reason": reason,
                "moderator": ctx.author.id,
                "moderator_name": f"{ctx.author.name}#{ctx.author.discriminator}",
                "timestamp": str(datetime.utcnow())
            }
        )
        
        await ctx.send(f"{member.mention} has been banned. Reason: {reason}")
    
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
                
                self.db.log_action(
                    user.id,
                    "unban",
                    {
                        "reason": "Unbanned by moderator",
                        "moderator": ctx.author.id,
                        "moderator_name": f"{ctx.author.name}#{ctx.author.discriminator}",
                        "timestamp": str(datetime.utcnow())
                    }
                )
                
                await ctx.send(f"{user.mention} has been unbanned.")
                return

async def setup(bot):
    await bot.add_cog(Moderation(bot))