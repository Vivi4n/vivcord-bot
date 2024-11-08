from discord.ext import commands
import discord
import aiohttp
import logging
from datetime import datetime

class AnimeCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger('AnimeCommands')
        self.base_api_url = "https://nekos.best/api/v2/"
        self.session = None

    async def cog_load(self):
        self.session = aiohttp.ClientSession()

    async def cog_unload(self):
        if self.session:
            await self.session.close()

    async def _fetch_anime_image(self, ctx, endpoint: str, title: str):
        try:
            async with self.session.get(f"{self.base_api_url}{endpoint}") as response:
                if response.status == 200:
                    data = await response.json()
                    results = data.get('results', [])
                    if not results:
                        await ctx.send("Sorry, couldn't find an image right now. Try again later!")
                        return

                    image_data = results[0]
                    image_url = image_data.get('url')
                    artist = image_data.get('artist_name')

                    if not image_url:
                        await ctx.send("Sorry, couldn't find an image right now. Try again later!")
                        return

                    embed = discord.Embed(
                        title=title,
                        color=discord.Color.purple(),
                        timestamp=datetime.utcnow()
                    )
                    embed.set_image(url=image_url)
                    if artist:
                        embed.set_footer(text=f"Artist: {artist} | Powered by nekos.best")
                    else:
                        embed.set_footer(text="Powered by nekos.best")

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
        """Get a random SFW anime waifu image"""
        await self._fetch_anime_image(ctx, "waifu", "Random Waifu")

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def husbando(self, ctx):
        """Get a random SFW anime husbando image"""
        await self._fetch_anime_image(ctx, "husbando", "Random Husbando")

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def neko(self, ctx):
        """Get a random SFW neko image"""
        await self._fetch_anime_image(ctx, "neko", "Random Neko")
    
    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def kitsune(self, ctx):
        """Get a random SFW kitsune image"""
        await self._fetch_anime_image(ctx, "kitsune", "Random Kitsune")
    
    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def pat(self, ctx):
        """Get a random anime patting gif"""
        await self._fetch_anime_image(ctx, "pat", "Headpat!")

    @waifu.error
    @husbando.error
    @neko.error
    @kitsune.error
    @pat.error
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