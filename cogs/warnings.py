from discord.ext import commands
import discord
from utils.database import Database
from datetime import datetime

class Warnings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database('data/user_logs.json')
    
    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def warn(self, ctx, member: discord.Member, *, reason=None):
        """Warn a member"""
        self.db.log_action(
            member.id,
            "warning",
            {
                "reason": reason,
                "moderator": ctx.author.id,
                "moderator_name": f"{ctx.author.name}#{ctx.author.discriminator}",
                "timestamp": str(datetime.utcnow())
            }
        )
        
        await ctx.send(f"{member.mention} has been warned. Reason: {reason}")

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def warnings(self, ctx, member: discord.Member):
        """Check warnings for a member"""
        user_id = str(member.id)
        if user_id not in self.db.data or not self.db.data[user_id]["warnings"]:
            await ctx.send(f"{member.mention} has no warnings.")
            return
        
        embed = discord.Embed(title=f"Warnings for {member.name}", color=discord.Color.orange())
        for i, warning in enumerate(self.db.data[user_id]["warnings"], 1):
            moderator = ctx.guild.get_member(int(warning["moderator"]))
            embed.add_field(
                name=f"Warning {i}",
                value=f"Reason: {warning['reason']}\n"
                      f"Date: {warning['timestamp']}\n"
                      f"Moderator: {warning['moderator_name']}",
                inline=False
            )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Warnings(bot))