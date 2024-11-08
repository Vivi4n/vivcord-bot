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

    async def _fetch_anime_image(self, ctx, endpoint: str, title: str, mentioned_user=None):
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
                    
                    if mentioned_user:
                        if endpoint in ['pat', 'hug', 'kiss', 'highfive', 'happy', 'laugh', 'poke', 'wave']:
                            embed.description = f"{ctx.author.mention} {endpoint}s {mentioned_user.mention}"
                        elif endpoint == 'cry':
                            embed.description = f"{ctx.author.mention} cries with {mentioned_user.mention}"
                        elif endpoint == 'dance':
                            embed.description = f"{ctx.author.mention} dances with {mentioned_user.mention}"
                        elif endpoint == 'baka':
                            embed.description = f"{ctx.author.mention} calls {mentioned_user.mention} baka!"
                        elif endpoint == 'feed':
                            embed.description = f"{ctx.author.mention} feeds {mentioned_user.mention}"
                        elif endpoint == 'bite':
                            embed.description = f"{ctx.author.mention} bites {mentioned_user.mention}"
                        elif endpoint == 'blush':
                            embed.description = f"{ctx.author.mention} blushes at {mentioned_user.mention}"
                        elif endpoint == 'bored':
                            embed.description = f"{ctx.author.mention} is bored with {mentioned_user.mention}"
                        elif endpoint == 'facepalm':
                            embed.description = f"{ctx.author.mention} facepalms at {mentioned_user.mention}"
                        elif endpoint == 'cuddle':
                            embed.description = f"{ctx.author.mention} cuddles with {mentioned_user.mention}"
                        elif endpoint == 'thumbsup':
                            embed.description = f"{ctx.author.mention} gives {mentioned_user.mention} a thumbs up"
                        elif endpoint == 'stare':
                            embed.description = f"{ctx.author.mention} stares at {mentioned_user.mention}"
                        elif endpoint == 'think':
                            embed.description = f"{ctx.author.mention} thinks about {mentioned_user.mention}"

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

    # Character Images
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

    # Interaction Commands
    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def pat(self, ctx, member: discord.Member = None):
        """Pat someone!"""
        await self._fetch_anime_image(ctx, "pat", "Headpat!", member)

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def hug(self, ctx, member: discord.Member = None):
        """Hug someone!"""
        await self._fetch_anime_image(ctx, "hug", "Hugs!", member)

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def kiss(self, ctx, member: discord.Member = None):
        """Kiss someone!"""
        await self._fetch_anime_image(ctx, "kiss", "Kiss!", member)

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def cuddle(self, ctx, member: discord.Member = None):
        """Cuddle with someone!"""
        await self._fetch_anime_image(ctx, "cuddle", "Cuddles!", member)

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def feed(self, ctx, member: discord.Member = None):
        """Feed someone!"""
        await self._fetch_anime_image(ctx, "feed", "Feeding time!", member)

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def bite(self, ctx, member: discord.Member = None):
        """Bite someone!"""
        await self._fetch_anime_image(ctx, "bite", "Nom!", member)

    # Emotion Commands
    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def cry(self, ctx, member: discord.Member = None):
        """Show that you're crying"""
        await self._fetch_anime_image(ctx, "cry", "Crying...", member)

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def dance(self, ctx, member: discord.Member = None):
        """Dance!"""
        await self._fetch_anime_image(ctx, "dance", "Dancing!", member)

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def laugh(self, ctx, member: discord.Member = None):
        """Show that you're laughing"""
        await self._fetch_anime_image(ctx, "laugh", "Hahaha!", member)

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def blush(self, ctx, member: discord.Member = None):
        """Show that you're blushing"""
        await self._fetch_anime_image(ctx, "blush", "B-baka!", member)

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def bored(self, ctx, member: discord.Member = None):
        """Show that you're bored"""
        await self._fetch_anime_image(ctx, "bored", "So boring...", member)

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def facepalm(self, ctx, member: discord.Member = None):
        """Facepalm at something"""
        await self._fetch_anime_image(ctx, "facepalm", "*facepalm*", member)

    # Action Commands
    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def wave(self, ctx, member: discord.Member = None):
        """Wave at someone!"""
        await self._fetch_anime_image(ctx, "wave", "Hello!", member)

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def poke(self, ctx, member: discord.Member = None):
        """Poke someone!"""
        await self._fetch_anime_image(ctx, "poke", "Poke poke!", member)

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def highfive(self, ctx, member: discord.Member = None):
        """High five someone!"""
        await self._fetch_anime_image(ctx, "highfive", "High five!", member)

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def stare(self, ctx, member: discord.Member = None):
        """Stare at someone"""
        await self._fetch_anime_image(ctx, "stare", "*stares*", member)

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def think(self, ctx, member: discord.Member = None):
        """Show that you're thinking"""
        await self._fetch_anime_image(ctx, "think", "*thinking*", member)

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def thumbsup(self, ctx, member: discord.Member = None):
        """Give a thumbs up!"""
        await self._fetch_anime_image(ctx, "thumbsup", "👍", member)

    # Error Handling
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(
                f"Please wait {error.retry_after:.1f} seconds before using this command again!",
                delete_after=5
            )
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send("Couldn't find that member!")
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