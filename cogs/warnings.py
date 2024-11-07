from discord.ext import commands
import discord
from utils.database import Database
from datetime import datetime

class Warnings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database('data/user_logs.json')

    async def log_to_modchannel(self, guild, embed):
        """Send log message to mod-logs channel"""
        mod_channel = discord.utils.get(guild.channels, name='mod-logs')
        if mod_channel:
            await mod_channel.send(embed=embed)

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def warn(self, ctx, member: discord.Member, *, reason=None):
        """Warn a member"""
        if member.top_role >= ctx.author.top_role:
            await ctx.send("nope.")
            return

        # Create embed for mod-logs
        embed = discord.Embed(
            title="Member Warned",
            color=discord.Color.yellow(),
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
            "warning",
            {
                "reason": reason,
                "moderator": ctx.author.id,
                "moderator_name": str(ctx.author),
                "timestamp": str(datetime.utcnow())
            }
        )
        
        await ctx.send(f"{member.mention} has been warned. Reason: {reason or 'No reason provided'}")

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def warnings(self, ctx, member: discord.Member):
        """Check warnings for a member"""
        user_data = self.db.ensure_user_data(str(member.id))
        
        if not user_data.get("warnings", []):
            await ctx.send(f"{member.mention} has no warnings.")
            return
        
        embed = discord.Embed(
            title=f"Warnings for {member.name}",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        
        for i, warning in enumerate(user_data["warnings"], 1):
            embed.add_field(
                name=f"Warning {i}",
                value=f"Reason: {warning.get('reason', 'No reason provided')}\n"
                      f"Date: {warning['timestamp']}\n"
                      f"Moderator: {warning['moderator_name']}",
                inline=False
            )
        
        embed.set_footer(text=f"User ID: {member.id}")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Warnings(bot))