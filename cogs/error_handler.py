from discord.ext import commands
import discord

class ErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        # Ignore CommandNotFound errors
        if isinstance(error, commands.CommandNotFound):
            return

        # Handle other errors
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("Oi wtf are you tryin' to do?")
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send("Fucker ain't here.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Required argument needed: {error.param.name}")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid argument.")
        else:
            await ctx.send(f"An error occurred: {str(error)}")

async def setup(bot):
    await bot.add_cog(ErrorHandler(bot))