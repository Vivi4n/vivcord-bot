import discord
from datetime import datetime

async def log_action(guild, action, member, moderator, reason):
    log_channel = discord.utils.get(guild.channels, name='mod-logs')
    if not log_channel:
        log_channel = await guild.create_text_channel('mod-logs')
        
    embed = discord.Embed(
        title=f"Moderation Action: {action}",
        color=discord.Color.blue(),
        timestamp=datetime.utcnow()
    )
    embed.add_field(name="User", value=f"{member.name}#{member.discriminator}", inline=True)
    embed.add_field(name="Moderator", value=f"{moderator.name}#{moderator.discriminator}", inline=True)
    embed.add_field(name="Reason", value=reason or "No reason provided", inline=False)
    await log_channel.send(embed=embed)