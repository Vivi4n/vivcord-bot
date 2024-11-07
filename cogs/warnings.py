from discord.ext import commands
import discord
from utils.database import Database
from utils.logger import log_action
from datetime import datetime

class Warnings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database('data/warnings.json')
    
    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def warn(self, ctx, member: discord.Member, *, reason=None):
        """Warn a member"""
        user_id = str(member.id)
        if user_id not in self.db.data:
            self.db.data[user_id] = []
        
        self.db.data[user_id].append({
            'reason': reason,
            'date': str(datetime.utcnow()),
            'moderator': ctx.author.id
        })
        self.db.save_data()
        
        await ctx.send(f"{member.mention} has been warned. Reason: {reason}")
        await log_action(ctx.guild, "Warning", member, ctx.author, reason)
    
    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def warnings(self, ctx, member: discord.Member):
        """Check warnings for a member"""
        user_id = str(member.id)
        if user_id not in self.db.data or not self.db.data[user_id]:
            await ctx.send(f"{member.mention} has no warnings.")
            return
        
        embed = discord.Embed(title=f"Warnings for {member.name}", color=discord.Color.orange())
        for i, warning in enumerate(self.db.data[user_id], 1):
            moderator = ctx.guild.get_member(warning['moderator'])
            embed.add_field(
                name=f"Warning {i}",
                value=f"Reason: {warning['reason']}\nDate: {warning['date']}\nModerator: {moderator.name if moderator else 'Unknown'}",
                inline=False
            )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Warnings(bot))