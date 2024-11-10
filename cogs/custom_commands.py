from discord.ext import commands
import discord
import json
import os
import logging
from datetime import datetime

class CustomCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger('CustomCommands')
        os.makedirs('data', exist_ok=True)
        self.commands_file = 'data/custom_commands.json'
        self.commands = self.load_commands()

    async def log_to_modchannel(self, guild, embed):
        mod_channel = discord.utils.get(guild.channels, name='mod-logs')
        if mod_channel:
            await mod_channel.send(embed=embed)

    def load_commands(self):
        if not os.path.exists(self.commands_file):
            return {}
        try:
            with open(self.commands_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load custom commands: {e}")
            return {}

    def save_commands(self):
        try:
            with open(self.commands_file, 'w') as f:
                json.dump(self.commands, f, indent=4)
        except Exception as e:
            self.logger.error(f"Failed to save custom commands: {e}")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        content = message.content.lower().strip()
        if content.startswith('no') and content.endswith('u'):
            parts = content.split()
            if len(parts) > 1 and all(part == 'no' for part in parts[:-1]) and parts[-1] == 'u':
                response = 'no ' * (len(parts)) + 'u'
                await message.channel.send(response)
                return

        if not message.content.startswith('!'):
            return

        guild_id = str(message.guild.id)
        if guild_id not in self.commands:
            return

        command = message.content[1:].split()[0]
        if command not in self.commands[guild_id]:
            return

        cmd_data = self.commands[guild_id][command]
        required_role = cmd_data["required_role"]

        if required_role != 0 and not any(role.id == required_role for role in message.author.roles):
            await message.channel.send("You don't have permission to use this command!")
            return

        response = cmd_data["response"]
        
        if cmd_data.get("requires_mention", False):
            target_user = None
            if message.reference and message.reference.resolved:
                target_user = message.reference.resolved.author
            elif message.mentions:
                target_user = message.mentions[0]
            
            if not target_user:
                await message.channel.send("Command requires user mention!")
                return
                
            response = response.replace("{mention}", target_user.mention)

        await message.channel.send(response)

    @commands.group(name='cc', invoke_without_command=True)
    async def custom_commands(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("Available subcommands: add, remove, list")

    @custom_commands.command(name='add')
    @commands.has_permissions(manage_messages=True)
    async def add_command(self, ctx, command: str, required_role: int, *, response: str):
        guild_id = str(ctx.guild.id)
        
        if guild_id not in self.commands:
            self.commands[guild_id] = {}
        
        if command in self.commands[guild_id]:
            await ctx.send(f"Command `{command}` already exists!")
            return

        requires_mention = "{mention}" in response

        self.commands[guild_id][command] = {
            "response": response,
            "required_role": required_role,
            "requires_mention": requires_mention
        }
        
        self.save_commands()
        mention_info = " (requires user mention)" if requires_mention else ""
        await ctx.send(f"Added command `{command}` with role requirement {required_role}{mention_info}")

        embed = discord.Embed(
            title="Custom Command Added",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Command", value=f"!{command}", inline=False)
        embed.add_field(name="Response", value=response, inline=False)
        embed.add_field(name="Required Role", value="Everyone" if required_role == 0 else f"Role ID: {required_role}", inline=False)
        embed.add_field(name="Added By", value=f"{ctx.author.mention} ({ctx.author.name})", inline=False)
        if requires_mention:
            embed.add_field(name="Note", value="This command requires a user mention", inline=False)
        
        await self.log_to_modchannel(ctx.guild, embed)

    @custom_commands.command(name='remove')
    @commands.has_permissions(manage_messages=True)
    async def remove_command(self, ctx, command: str):
        guild_id = str(ctx.guild.id)
        
        if guild_id in self.commands and command in self.commands[guild_id]:
            cmd_data = self.commands[guild_id][command]
            
            del self.commands[guild_id][command]
            self.save_commands()
            await ctx.send(f"Removed command `{command}`")

            embed = discord.Embed(
                title="Custom Command Removed",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Command", value=f"!{command}", inline=False)
            embed.add_field(name="Response", value=cmd_data["response"], inline=False)
            embed.add_field(name="Required Role", value="Everyone" if cmd_data["required_role"] == 0 else f"Role ID: {cmd_data['required_role']}", inline=False)
            embed.add_field(name="Removed By", value=f"{ctx.author.mention} ({ctx.author.name})", inline=False)
            
            await self.log_to_modchannel(ctx.guild, embed)
        else:
            await ctx.send(f"Command `{command}` not found!")

    @custom_commands.command(name='list')
    async def list_commands(self, ctx):
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
            mention_req = " (requires mention)" if data.get("requires_mention", False) else ""
            embed.add_field(
                name=f"!{cmd}",
                value=f"Required Role: {role_req}{mention_req}\nResponse: {data['response']}",
                inline=False
            )

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(CustomCommands(bot))