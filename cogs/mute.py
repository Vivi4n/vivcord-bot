from discord.ext import commands
import discord
from utils.database import Database
from datetime import datetime

class Mute(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database('data/user_logs.json')
    
    async def ensure_muted_role(self, guild):
        muted_role = discord.utils.get(guild.roles, name="Muted")
        if not muted_role:
            muted_role = await guild.create_role(name="Muted")
            for channel in guild.channels:
                await channel.set_permissions(muted_role, speak=False, send_messages=False)
        return muted_role
    
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def mute(self, ctx, member: discord.Member, *, reason=None):
        """Mute a member"""
        muted_role = await self.ensure_muted_role(ctx.guild)
        await member.add_roles(muted_role, reason=reason)
        
        self.db.log_action(
            member.id,
            "mute",
            {
                "reason": reason,
                "moderator": ctx.author.id,
                "moderator_name": f"{ctx.author.name}#{ctx.author.discriminator}",
                "timestamp": str(datetime.utcnow())
            }
        )
        
        await ctx.send(f"{member.mention} has been muted. Reason: {reason}")
    
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def unmute(self, ctx, member: discord.Member):
        """Unmute a member"""
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if muted_role in member.roles:
            await member.remove_roles(muted_role)
            
            self.db.log_action(
                member.id,
                "unmute",
                {
                    "reason": "Unmuted by moderator",
                    "moderator": ctx.author.id,
                    "moderator_name": f"{ctx.author.name}#{ctx.author.discriminator}",
                    "timestamp": str(datetime.utcnow())
                }
            )
            
            await ctx.send(f"{member.mention} has been unmuted.")

async def setup(bot):
    await bot.add_cog(Mute(bot))