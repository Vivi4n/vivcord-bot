from discord.ext import commands
import discord
import json
import os
import re
from typing import Optional
import logging

class CustomCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger('CustomCommands')
        self.commands_file = 'data/custom_commands.json'
        self.commands = self.load_commands()

    def load_commands(self):
        """Load custom commands from JSON file"""
        try:
            if os.path.exists(self.commands_file):
                with open(self.commands_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load custom commands: {e}")
        return {}

    def save_commands(self):
        """Save custom commands to JSON file"""
        try:
            os.makedirs(os.path.dirname(self.commands_file), exist_ok=True)
            with open(self.commands_file, 'w') as f:
                json.dump(self.commands, f, indent=4)
        except Exception as e:
            self.logger.error(f"Failed to save custom commands: {e}")

    @commands.group(name='cc', invoke_without_command=True)
    async def custom_commands(self, ctx):
        """Custom commands management"""
        await ctx.send("Available subcommands: add, remove, list")

    @custom_commands.command(name='add')
    @commands.has_permissions(manage_messages=True)
    async def add_command(self, ctx, command: str, required_role: int, *, response: str):
        """Add a custom command"""
        guild_id = str(ctx.guild.id)
        
        if guild_id not in self.commands:
            self.commands[guild_id] = {}
        
        # Check if command already exists
        if command in self.commands[guild_id]:
            await ctx.send(f"Command `{command}` already exists!")
            return

        # Check if command requires mention
        requires_mention = "{mention}" in response

        self.commands[guild_id][command] = {
            "response": response,
            "required_role": required_role,
            "requires_mention": requires_mention
        }
        
        self.save_commands()
        mention_info = " (requires user mention)" if requires_mention else ""
        await ctx.send(f"Added command `{command}` with role requirement {required_role}{mention_info}")

    @custom_commands.command(name='remove')
    @commands.has_permissions(manage_messages=True)
    async def remove_command(self, ctx, command: str):
        """Remove a custom command"""
        guild_id = str(ctx.guild.id)
        
        if guild_id in self.commands and command in self.commands[guild_id]:
            del self.commands[guild_id][command]
            self.save_commands()
            await ctx.send(f"Removed command `{command}`")
        else:
            await ctx.send(f"Command `{command}` not found!")

    @custom_commands.command(name='list')
    async def list_commands(self, ctx):
        """List all custom commands"""
        guild_id = str(ctx.guild.id)
        
        if guild_id not in self.commands or not self.commands[guild_id]:
            await ctx.send("No custom commands set up!")
            return

        embed = discord.Embed(
            title="Custom Commands",
            color=discord.Color.blue(),
            description="List of all custom commands:"
        )

        for cmd, data in self.commands[guild_id].items():
            role_req = "Everyone" if data["required_role"] == 0 else f"Role ID: {data['required_role']}"
            mention_req = " (requires mention)" if data["requires_mention"] else ""
            embed.add_field(
                name=f"!{cmd}",
                value=f"Required Role: {role_req}{mention_req}\nResponse: {data['response']}",
                inline=False
            )

        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle custom commands in messages"""
        if message.author.bot or not message.content.startswith('!'):
            return

        guild_id = str(message.guild.id)
        if guild_id not in self.commands:
            return

        command = message.content[1:].split()[0]
        if command not in self.commands[guild_id]:
            return

        cmd_data = self.commands[guild_id][command]
        required_role = cmd_data["required_role"]

        # Check role permission
        if required_role != 0 and not any(role.id == required_role for role in message.author.roles):
            await message.channel.send("Can't use that. Continued abuse will result in your demise.")
            return

        response = cmd_data["response"]
        
        # Handle mention if command requires it
        if cmd_data["requires_mention"]:
            # Check for replied message
            target_user = None
            if message.reference and message.reference.resolved:
                target_user = message.reference.resolved.author
            # Check for mentions
            elif message.mentions:
                target_user = message.mentions[0]
            
            if not target_user:
                await message.channel.send("Command requires user mention!")
                return
                
            response = response.replace("{mention}", target_user.mention)

        await message.channel.send(response)

async def setup(bot):
    await bot.add_cog(CustomCommands(bot))