from discord.ext import commands
import discord
import aiohttp
import logging
from datetime import datetime

class AnimeCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger('AnimeCommands')
        self.waifu_api_url = "https://api.waifu.pics/sfw/waifu"
        self.husbando_api_url = "https://api.waifu.pics/sfw/husbando"
        self.session = None

    async def cog_load(self):
        self.session = aiohttp.ClientSession()

    async def cog_unload(self):
        if self.session:
            await self.session.close()

    async def _fetch_anime_image(self, ctx, api_url: str, title: str):
        try:
            async with self.session.get(api_url) as response:
                if response.status == 200:
                    data = await response.json()
                    image_url = data.get('url')

                    if not image_url:
                        await ctx.send("Sorry, couldn't find an image right now. Try again later!")
                        return

                    embed = discord.Embed(
                        title=title,
                        color=discord.Color.purple(),
                        timestamp=datetime.utcnow()
                    )
                    embed.set_image(url=image_url)
                    embed.set_footer(text="Powered by waifu.pics | SFW Content Only")

                    await ctx.send(embed=embed)
                else:
                    await ctx.send("Sorry, there was an error accessing the anime image service.")

        except aiohttp.ClientError as e:
            self.logger.error(f"API request failed: {str(e)}")
            await ctx.send("Sorry, there was an error connecting to the anime image service.")
        except Exception as e:
            self.logger.error(f"Unexpected error in anime command: {str(e)}")
            await ctx.send("An unexpected error occurred. Please try again later.")

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def waifu(self, ctx):
        """Get a random SFW anime character image"""
        await self._fetch_anime_image(ctx, self.waifu_api_url, "Random Anime Character")

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def husbando(self, ctx):
        """Get a random SFW male anime character image"""
        await self._fetch_anime_image(ctx, self.husbando_api_url, "Random Male Anime Character")

    @waifu.error
    @husbando.error
    async def anime_command_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(
                f"Please wait {error.retry_after:.1f} seconds before using this command again!",
                delete_after=5
            )
        else:
            self.logger.error(f"Unhandled error in anime command: {str(error)}")
            await ctx.send("An error occurred while processing your request.")

async def setup(bot):
    try:
        import aiohttp
    except ImportError:
        import subprocess
        subprocess.check_call(["pip", "install", "aiohttp"])
    
    await bot.add_cog(AnimeCommands(bot))