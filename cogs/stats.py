from discord.ext import commands
import discord
from utils.database import Database
from datetime import datetime, timedelta
import os
import json

class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database('data/user_logs.json')
        self.voice_time_tracker = {}

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.author.bot:
            user_id = str(message.author.id)
            user_data = self.db.ensure_user_data(user_id)
            user_data["messages"] += 1
            user_data["last_seen"] = str(datetime.utcnow())
            self.db.save_data()

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if not message.author.bot:
            user_id = str(message.author.id)
            user_data = self.db.ensure_user_data(user_id)
            user_data["message_deletes"] += 1
            self.db.save_data()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        user_id = str(member.id)
        
        # Member joined voice channel
        if before.channel is None and after.channel is not None:
            self.voice_time_tracker[user_id] = datetime.utcnow()
        
        # Member left voice channel
        elif before.channel is not None and after.channel is None:
            if user_id in self.voice_time_tracker:
                start_time = self.voice_time_tracker[user_id]
                duration = datetime.utcnow() - start_time
                minutes = duration.total_seconds() / 60
                
                user_data = self.db.ensure_user_data(user_id)
                user_data["voice_time"] += minutes
                self.db.save_data()
                del self.voice_time_tracker[user_id]

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def stats(self, ctx, member: discord.Member = None):
        """Display comprehensive stats for a user"""
        member = member or ctx.author
        user_id = str(member.id)
        
        user_data = self.db.ensure_user_data(user_id)
        
        # Create embed
        embed = discord.Embed(
            title=f"Statistics for {member.display_name}",
            color=member.color,
            timestamp=datetime.utcnow()
        )
        
        # Basic Info
        embed.add_field(
            name="Basic Information",
            value=f"Join Date: {user_data.get('join_date', 'Unknown')}\n"
                  f"Last Seen: {user_data.get('last_seen', 'Never')}\n"
                  f"Messages Sent: {user_data.get('messages', 0)}\n"
                  f"Messages Deleted: {user_data.get('message_deletes', 0)}\n"
                  f"Voice Time: {round(user_data.get('voice_time', 0), 2)} minutes",
            inline=False
        )
        
        # Moderation Stats
        warnings_count = len(user_data.get('warnings', []))
        kicks_count = len(user_data.get('kicks', []))
        bans_count = len(user_data.get('bans', []))
        mutes_count = len(user_data.get('mutes', []))
        
        embed.add_field(
            name="Moderation History",
            value=f"Warnings: {warnings_count}\n"
                  f"Kicks: {kicks_count}\n"
                  f"Bans: {bans_count}\n"
                  f"Mutes: {mutes_count}",
            inline=False
        )
        
        # Recent Actions
        recent_actions = user_data.get('action_history', [])[-5:]  # Last 5 actions
        if recent_actions:
            action_text = []
            for action in recent_actions:
                action_type = action['type'].title()
                details = action['details']
                reason = details.get('reason', 'No reason')
                timestamp = action['timestamp']
                action_text.append(f"{action_type}: {reason} ({timestamp})")
            action_text = "\n".join(action_text)
        else:
            action_text = "No recent actions"
            
        embed.add_field(
            name="Recent Actions",
            value=action_text,
            inline=False
        )
        
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def export_logs(self, ctx, member: discord.Member):
        """Export complete log history for a user"""
        user_id = str(member.id)
        user_data = self.db.ensure_user_data(user_id)
        
        # Create a formatted text file
        log_text = [
            f"Log Export for {member.display_name} (ID: {member.id})",
            f"Generated at: {datetime.utcnow()}",
            "\n=== Basic Information ===",
            f"Join Date: {user_data.get('join_date', 'Unknown')}",
            f"Last Seen: {user_data.get('last_seen', 'Never')}",
            f"Total Messages: {user_data.get('messages', 0)}",
            f"Deleted Messages: {user_data.get('message_deletes', 0)}",
            f"Voice Time: {round(user_data.get('voice_time', 0), 2)} minutes",
            "\n=== Action History ==="
        ]
        
        for action in user_data.get('action_history', []):
            log_text.append(
                f"\n[{action['timestamp']}] {action['type'].upper()}:"
                f"\nReason: {action['details'].get('reason', 'No reason provided')}"
                f"\nModerator: {action['details'].get('moderator_name', 'Unknown')}"
            )
        
        # Save to file
        filename = f"logs_{member.id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(log_text))
            
        # Send file to channel
        await ctx.send(f"Log export for {member.mention}", file=discord.File(filename))
        
        # Clean up file
        os.remove(filename)
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def debug_stats(self, ctx, member: discord.Member):
        """Debug command to show raw data"""
        user_id = str(member.id)
        self.db.debug_print_user(user_id)
        
        # Also load and show the data directly from file
        try:
            with open('data/user_logs.json', 'r') as f:
                data = json.load(f)
                if user_id in data:
                    user_data = data[user_id]
                    warnings = len(user_data.get('warnings', []))
                    action_history = len(user_data.get('action_history', []))
                    await ctx.send(f"Debug info for {member.name}:\n"
                                 f"Warnings count: {warnings}\n"
                                 f"Action history count: {action_history}\n"
                                 f"Raw data has been printed to logs")
                else:
                    await ctx.send(f"No data found for {member.name}")
        except Exception as e:
            await ctx.send(f"Error reading data: {str(e)}")

async def setup(bot):
    await bot.add_cog(Stats(bot))