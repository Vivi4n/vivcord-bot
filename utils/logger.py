import os
import discord
from discord.ext import commands
from datetime import datetime
import logging

class Logging(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger('Logging')

    @commands.Cog.listener()
    async def on_message(self, message):
        """Log message events"""
        if not message.author.bot:
            self.logger.info(
                f"Message sent by {message.author} (ID: {message.author.id}) "
                f"in #{message.channel.name} ({message.guild.name})"
            )

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        """Log message deletions"""
        if not message.author.bot:
            self.logger.info(
                f"Message by {message.author} (ID: {message.author.id}) "
                f"deleted in #{message.channel.name} ({message.guild.name})"
            )

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Log member joins"""
        self.logger.info(
            f"Member {member} (ID: {member.id}) joined {member.guild.name}"
        )

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Log member leaves"""
        self.logger.info(
            f"Member {member} (ID: {member.id}) left {member.guild.name}"
        )

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        """Log member bans"""
        self.logger.info(
            f"Member {user} (ID: {user.id}) was banned from {guild.name}"
        )

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        """Log member unbans"""
        self.logger.info(
            f"Member {user} (ID: {user.id}) was unbanned from {guild.name}"
        )

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def getlogs(self, ctx, days: int = 1):
        """Get bot logs for the specified number of days"""
        try:
            if not os.path.exists('bot.log'):
                await ctx.send("No logs found.")
                return

            with open('bot.log', 'r', encoding='utf-8') as f:
                logs = f.readlines()

            # Filter logs by date
            current_time = datetime.utcnow()
            filtered_logs = []
            for log in logs:
                try:
                    log_date = datetime.strptime(log.split(' - ')[0], '%Y-%m-%d %H:%M:%S,%f')
                    if (current_time - log_date).days <= days:
                        filtered_logs.append(log)
                except (ValueError, IndexError):
                    continue

            if not filtered_logs:
                await ctx.send(f"No logs found for the last {days} day(s).")
                return

            # Write filtered logs to temporary file
            temp_filename = f'logs_{ctx.guild.id}_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.txt'
            with open(temp_filename, 'w', encoding='utf-8') as f:
                f.writelines(filtered_logs)

            # Send file
            await ctx.send(
                f"Logs for the last {days} day(s)",
                file=discord.File(temp_filename)
            )

            # Clean up
            os.remove(temp_filename)

        except Exception as e:
            self.logger.error(f"Error in getlogs: {str(e)}")
            await ctx.send("An error occurred while retrieving logs.")

async def setup(bot):
    await bot.add_cog(Logging(bot))