from discord.ext import commands
import discord
from datetime import datetime, timedelta
import os

class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
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
        
        if before.channel is None and after.channel is not None:
            self.voice_time_tracker[user_id] = datetime.utcnow()
        
        elif before.channel is not None and after.channel is None:
            if user_id in self.voice_time_tracker:
                start_time = self.voice_time_tracker[user_id]
                duration = datetime.utcnow() - start_time
                minutes = duration.total_seconds() / 60
                
                user_data = self.db.ensure_user_data(user_id)
                user_data["voice_time"] += minutes
                self.db.save_data()
                del self.voice_time_tracker[user_id]

    def format_datetime(self, date_str):
        try:
            dt = datetime.fromisoformat(date_str)
            return dt.strftime("%d/%m/%Y %H:%M")
        except (ValueError, TypeError):
            return "Unknown"

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def stats(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        user_id = str(member.id)
        
        user_data = self.db.ensure_user_data(user_id)
        
        embed = discord.Embed(
            title=f"Statistics for {member.display_name}",
            color=member.color,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="Basic Information",
            value=f"Join Date: {self.format_datetime(user_data.get('join_date', 'Unknown'))}\n"
                  f"Last Seen: {self.format_datetime(user_data.get('last_seen', 'Never'))}\n"
                  f"Messages Sent: {user_data.get('messages', 0)}\n"
                  f"Messages Deleted: {user_data.get('message_deletes', 0)}\n"
                  f"Voice Time: {round(user_data.get('voice_time', 0), 2)} minutes",
            inline=False
        )
        
        embed.add_field(
            name="Moderation History",
            value=f"Warnings: {len(user_data.get('warnings', []))}, "
                  f"Kicks: {len(user_data.get('kicks', []))}, "
                  f"Bans: {len(user_data.get('bans', []))}, "
                  f"Mutes: {len(user_data.get('mutes', []))}",
            inline=False
        )
        
        recent_actions = user_data.get('action_history', [])[-5:]
        if recent_actions:
            action_text = []
            for action in recent_actions:
                action_type = action['type'].title()
                details = action['details']
                reason = details.get('reason', 'No reason')
                timestamp = self.format_datetime(action['timestamp'])
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
        user_id = str(member.id)
        user_data = self.db.ensure_user_data(user_id)
        
        log_text = [
            f"Log Export for {member.display_name} (ID: {member.id})",
            f"Generated at: {datetime.utcnow().strftime('%d/%m/%Y %H:%M')}",
            "\n=== Basic Information ===",
            f"Join Date: {self.format_datetime(user_data.get('join_date', 'Unknown'))}",
            f"Last Seen: {self.format_datetime(user_data.get('last_seen', 'Never'))}",
            f"Total Messages: {user_data.get('messages', 0)}",
            f"Deleted Messages: {user_data.get('message_deletes', 0)}",
            f"Voice Time: {round(user_data.get('voice_time', 0), 2)} minutes",
            "\n=== Action History ==="
        ]
        
        for action in user_data.get('action_history', []):
            log_text.append(
                f"\n[{self.format_datetime(action['timestamp'])}] {action['type'].upper()}:"
                f"\nReason: {action['details'].get('reason', 'No reason provided')}"
                f"\nModerator: {action['details'].get('moderator_name', 'Unknown')}"
            )
        
        filename = f"logs_{member.id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(log_text))
            
        await ctx.send(f"Log export for {member.mention}", file=discord.File(filename))
        
        os.remove(filename)

async def setup(bot):
    await bot.add_cog(Stats(bot))