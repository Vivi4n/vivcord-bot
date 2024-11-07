from discord.ext import commands
import discord
from utils.database import Database
from datetime import datetime
import logging

class Warnings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database('data/user_logs.json')
        self.logger = logging.getLogger('Warnings')

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def warn(self, ctx, member: discord.Member, *, reason=None):
        """Warn a member"""
        if member.top_role >= ctx.author.top_role:
            await ctx.send("nope.")
            return

        self.logger.info(f"Warning user {member.id} ({member.name})")
        
        warning_data = {
            "reason": reason or "No reason provided",
            "moderator": ctx.author.id,
            "moderator_name": str(ctx.author),
            "timestamp": str(datetime.utcnow())
        }
        
        # Log to database
        try:
            self.db.log_action(
                member.id,
                "warnings",  # Using plural form consistently
                warning_data
            )
            self.logger.info(f"Successfully logged warning for {member.id}")
        except Exception as e:
            self.logger.error(f"Failed to log warning: {str(e)}")
            await ctx.send("Failed to log warning. Please check the bot logs.")
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
        try:
            await self.log_to_modchannel(ctx.guild, embed)
        except Exception as e:
            self.logger.error(f"Failed to send to mod channel: {str(e)}")
        
        await ctx.send(f"{member.mention} has been warned. Reason: {reason or 'No reason provided'}")

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def warnings(self, ctx, member: discord.Member):
        """Check warnings for a member"""
        self.logger.info(f"Checking warnings for {member.id} ({member.name})")
        
        user_data = self.db.ensure_user_data(str(member.id))
        warnings = user_data.get("warnings", [])
        
        self.logger.info(f"Found {len(warnings)} warnings for {member.id}")
        
        if not warnings:
            await ctx.send(f"{member.mention} has no warnings.")
            return
        
        embed = discord.Embed(
            title=f"Warnings for {member.name}",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        
        for i, warning in enumerate(warnings, 1):
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