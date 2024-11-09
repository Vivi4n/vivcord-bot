from discord.ext import commands
import discord
import aiohttp
import logging
from datetime import datetime
from typing import Optional, Dict, ClassVar
from functools import partial

class AnimeCommands(commands.Cog):
    """A cog for anime-related commands using the nekos.best API"""
    
    # Class constants
    BASE_API_URL: ClassVar[str] = "https://nekos.best/api/v2/"
    
    # Map endpoints to their interaction descriptions
    INTERACTION_DESCRIPTIONS: ClassVar[Dict[str, str]] = {
        "pat": "{author} pats {target}",
        "hug": "{author} hugs {target}",
        "kiss": "{author} kisses {target}",
        "highfive": "{author} high-fives {target}",
        "happy": "{author} is happy with {target}",
        "laugh": "{author} laughs with {target}",
        "poke": "{author} pokes {target}",
        "wave": "{author} waves at {target}",
        "cry": "{author} cries with {target}",
        "dance": "{author} dances with {target}",
        "baka": "{author} calls {target} baka!",
        "feed": "{author} feeds {target}",
        "bite": "{author} bites {target}",
        "blush": "{author} blushes at {target}",
        "bored": "{author} is bored with {target}",
        "facepalm": "{author} facepalms at {target}",
        "cuddle": "{author} cuddles with {target}",
        "thumbsup": "{author} gives {target} a thumbs up",
        "stare": "{author} stares at {target}",
        "think": "{author} thinks about {target}"
    }

    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger('AnimeCommands')
        self.session: Optional[aiohttp.ClientSession] = None
        self._setup_interaction_commands()

    def _setup_interaction_commands(self):
        """Set up interaction commands dynamically"""
        for cmd_name in self.INTERACTION_DESCRIPTIONS:
            # Create the interaction command
            @commands.command(name=cmd_name)
            @commands.cooldown(1, 5, commands.BucketType.user)
            async def interaction_cmd(self, ctx, member: discord.Member = None, cmd_name=cmd_name):
                await self._fetch_anime_image(ctx, cmd_name, cmd_name.title() + "!", member)

            # Set the command's help text
            interaction_cmd.help = f"Send a {cmd_name} interaction to someone!"
            
            # Add the command to the cog
            interaction_cmd = commands.command(name=cmd_name)(interaction_cmd)
            setattr(self.__class__, cmd_name, interaction_cmd)

    async def cog_load(self):
        """Initialize aiohttp session when cog loads"""
        self.session = aiohttp.ClientSession()

    async def cog_unload(self):
        """Cleanup aiohttp session when cog unloads"""
        if self.session:
            await self.session.close()
            self.session = None

    def create_embed(self, title: str, image_url: str, artist: Optional[str], 
                    interaction_msg: Optional[str] = None) -> discord.Embed:
        """Create a standardized embed for anime images"""
        embed = discord.Embed(
            title=title,
            color=discord.Color.purple(),
            timestamp=datetime.utcnow()
        )
        
        if interaction_msg:
            embed.description = interaction_msg
            
        embed.set_image(url=image_url)
        footer_text = f"Artist: {artist} | " if artist else ""
        embed.set_footer(text=f"{footer_text}Powered by nekos.best")
        
        return embed

    async def _fetch_anime_image(self, ctx: commands.Context, endpoint: str, 
                               title: str, mentioned_user: Optional[discord.Member] = None) -> None:
        """Fetch and send an anime image from the API"""
        if not self.session:
            await ctx.send("Bot is not properly initialized. Please try again later.")
            return

        try:
            async with self.session.get(f"{self.BASE_API_URL}{endpoint}") as response:
                if response.status != 200:
                    await ctx.send(f"API returned status {response.status}. Please try again later.")
                    return

                data = await response.json()
                results = data.get('results', [])
                if not results:
                    await ctx.send("No images found. Please try again later.")
                    return

                image_data = results[0]
                image_url = image_data.get('url')
                if not image_url:
                    await ctx.send("Invalid image data received. Please try again later.")
                    return

                interaction_msg = None
                if mentioned_user and endpoint in self.INTERACTION_DESCRIPTIONS:
                    interaction_msg = self.INTERACTION_DESCRIPTIONS[endpoint].format(
                        author=ctx.author.mention,
                        target=mentioned_user.mention
                    )

                embed = self.create_embed(
                    title=title,
                    image_url=image_url,
                    artist=image_data.get('artist_name'),
                    interaction_msg=interaction_msg
                )
                
                await ctx.send(embed=embed)

        except aiohttp.ClientError as e:
            self.logger.error(f"API request failed: {str(e)}")
            await ctx.send("Failed to connect to the image service. Please try again later.")
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
            await ctx.send("An unexpected error occurred. Please try again later.")

    # Character Commands
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

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Centralized error handling for the cog"""
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(
                f"Please wait {error.retry_after:.1f} seconds before using this command again.",
                delete_after=5
            )
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send("Couldn't find that member! Please mention a valid member.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid argument provided. Please check the command usage.")
        else:
            self.logger.error(f"Unhandled error: {str(error)}")
            await ctx.send("An error occurred while processing your request.")

async def setup(bot):
    await bot.add_cog(AnimeCommands(bot))