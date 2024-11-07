from discord.ext import commands
import discord
from datetime import datetime, timedelta
from utils.database import Database

class Logging(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database('data/user_logs.json')
        self.voice_time_tracker = {}
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.author.bot:
            user_id = str(message.author.id)
            if user_id in self.db.data:
                self.db.data[user_id]["messages"] += 1
                self.db.data[user_id]["last_seen"] = str(datetime.utcnow())
                self.db.save_data()
    
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if not message.author.bot:
            user_id = str(message.author.id)
            if user_id in self.db.data:
                self.db.data[user_id]["message_deletes"] += 1
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
                
                if user_id in self.db.data:
                    self.db.data[user_id]["voice_time"] += minutes
                    self.db.save_data()
                del self.voice_time_tracker[user_id]

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def stats(self, ctx, member: discord.Member = None):
        """Display comprehensive stats for a user"""
        member = member or ctx.author
        user_id = str(member.id)
        
        if user_id not in self.db.data:
            await ctx.send(f"No data available for {member.mention}")
            return
        
        user_data = self.db.data[user_id]
        
        # Create embed
        embed = discord.Embed(
            title=f"Statistics for {member.name}#{member.discriminator}",
            color=member.color,
            timestamp=datetime.utcnow()
        )
        
        # Basic Info
        embed.add_field(
            name="Basic Information",
            value=f"Join Date: {user_data['join_date']}\n"
                  f"Last Seen: {user_data['last_seen']}\n"
                  f"Messages Sent: {user_data['messages']}\n"
                  f"Messages Deleted: {user_data['message_deletes']}\n"
                  f"Voice Time: {round(user_data['voice_time'], 2)} minutes",
            inline=False
        )
        
        # Moderation Stats
        embed.add_field(
            name="Moderation History",
            value=f"Warnings: {len(user_data['warnings'])}\n"
                  f"Kicks: {len(user_data['kicks'])}\n"
                  f"Bans: {len(user_data['bans'])}\n"
                  f"Mutes: {len(user_data['mutes'])}",
            inline=False
        )
        
        # Recent Actions
        recent_actions = user_data['action_history'][-5:]  # Last 5 actions
        if recent_actions:
            action_text = "\n".join(
                f"{action['type'].title()}: {action['details']['reason']} ({action['timestamp']})"
                for action in recent_actions
            )
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
        if user_id not in self.db.data:
            await ctx.send(f"No data available for {member.mention}")
            return
            
        user_data = self.db.data[user_id]
        
        # Create a formatted text file
        log_text = [
            f"Log Export for {member.name}#{member.discriminator} (ID: {member.id})",
            f"Generated at: {datetime.utcnow()}",
            "\n=== Basic Information ===",
            f"Join Date: {user_data['join_date']}",
            f"Last Seen: {user_data['last_seen']}",
            f"Total Messages: {user_data['messages']}",
            f"Deleted Messages: {user_data['message_deletes']}",
            f"Voice Time: {round(user_data['voice_time'], 2)} minutes",
            "\n=== Action History ===",
        ]
        
        for action in user_data['action_history']:
            log_text.append(
                f"\n[{action['timestamp']}] {action['type'].upper()}:"
                f"\nReason: {action['details'].get('reason', 'No reason provided')}"
                f"\nModerator: {action['details'].get('moderator', 'Unknown')}"
            )
        
        # Save to file
        filename = f"logs_{member.id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(log_text))
            
        # Send file to channel
        await ctx.send(f"Log export for {member.mention}", file=discord.File(filename))
        
        # Clean up file
        os.remove(filename)

async def setup(bot):
    await bot.add_cog(Logging(bot))