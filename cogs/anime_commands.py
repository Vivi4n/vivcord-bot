from discord.ext import commands
import discord
import aiohttp
import logging
from datetime import datetime
from typing import Optional, Dict, ClassVar, Callable
from functools import wraps

def anime_command(name: str, title: str, help_text: str):
    def decorator(func: Callable):
        @commands.command(name=name)
        @commands.cooldown(1, 5, commands.BucketType.user)
        @wraps(func)
        async def wrapper(self, ctx, member: Optional[discord.Member] = None):
            if not member and ctx.message.reference:
                referenced_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
                if referenced_msg:
                    member = referenced_msg.author
            
            # Use endpoint parameter instead
            endpoint = getattr(func, '_endpoint', name)
            await self._fetch_anime_image(ctx, endpoint, title, member)
        wrapper.__doc__ = help_text
        return wrapper
    return decorator

class AnimeCommands(commands.Cog):   
    BASE_API_URL: ClassVar[str] = "https://nekos.best/api/v2/"
    
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
        "think": "{author} thinks about {target}",
        "handhold": "{author} holds hands with {target}",
        "handshake": "{author} shakes hands with {target}",
        "kick": "{author} kicks {target}",
        "lurk": "{author} lurks at {target}",
        "nod": "{author} nods at {target}",
        "nom": "{author} noms on {target}",
        "nope": "{author} says nope to {target}",
        "peck": "{author} pecks {target}",
        "pout": "{author} pouts at {target}",
        "punch": "{author} punches {target}",
        "shoot": "{author} shoots at {target}",
        "shrug": "{author} shrugs at {target}",
        "slap": "{author} slaps {target}",
        "sleep": "{author} falls asleep on {target}",
        "smile": "{author} smiles at {target}",
        "smug": "{author} gives {target} a smug look",
        "tickle": "{author} tickles {target}",
        "wink": "{author} winks at {target}",
        "yawn": "{author} yawns at {target}",
        "yeet": "{author} yeets {target}"
    }

    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger('AnimeCommands')
        self.session: Optional[aiohttp.ClientSession] = None

    async def cog_load(self):
        self.session = aiohttp.ClientSession()

    async def cog_unload(self):
        if self.session:
            await self.session.close()
            self.session = None

    def create_embed(self, title: str, image_url: str, artist: Optional[str], 
        interaction_msg: Optional[str] = None,
        member: Optional[discord.Member] = None) -> discord.Embed:
        color = member.color if member and member.color != discord.Color.default() else discord.Color.purple()

        embed = discord.Embed(
            title=title,
            color=color,
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
                target_member = mentioned_user
                if mentioned_user and endpoint in self.INTERACTION_DESCRIPTIONS:
                    interaction_msg = self.INTERACTION_DESCRIPTIONS[endpoint].format(
                        author=ctx.author.mention,
                        target=mentioned_user.mention
                    )
                
                elif not mentioned_user:
                    target_member =  ctx.author

                embed = self.create_embed(
                    title=title,
                    image_url=image_url,
                    artist=image_data.get('artist_name'),
                    interaction_msg=interaction_msg,
                    member=target_member
                )
                
                await ctx.send(embed=embed)

        except aiohttp.ClientError as e:
            self.logger.error(f"API request failed: {str(e)}")
            await ctx.send("Failed to connect to the image service. Please try again later.")
        except Exception as e:
            self.logger.error(f"Unexpected error in _fetch_anime_image: {str(e)}")
            await ctx.send("An error occurred while processing your request.")

    @anime_command(name="waifu", title="Random Waifu", help_text="Get a random SFW anime waifu image")
    async def waifu(self, ctx, member: discord.Member = None): pass

    @anime_command(name="husbando", title="Random Husbando", help_text="Get a random SFW anime husbando image")
    async def husbando(self, ctx, member: discord.Member = None): pass

    @anime_command(name="neko", title="Random Neko", help_text="Get a random SFW neko image")
    async def neko(self, ctx, member: discord.Member = None): pass

    @anime_command(name="kitsune", title="Random Kitsune", help_text="Get a random SFW kitsune image")
    async def kitsune(self, ctx, member: discord.Member = None): pass

    # Interaction Commands
    @anime_command(name="pat", title="Headpat!", help_text="Pat someone!")
    async def pat(self, ctx, member: discord.Member = None): pass

    @anime_command(name="hug", title="Hugs!", help_text="Hug someone!")
    async def hug(self, ctx, member: discord.Member = None): pass

    @anime_command(name="kiss", title="Kiss!", help_text="Kiss someone!")
    async def kiss(self, ctx, member: discord.Member = None): pass

    @anime_command(name="highfive", title="High Five!", help_text="High five someone!")
    async def highfive(self, ctx, member: discord.Member = None): pass

    @anime_command(name="happy", title="Happy!", help_text="Be happy with someone!")
    async def happy(self, ctx, member: discord.Member = None): pass

    @anime_command(name="laugh", title="Hahaha!", help_text="Laugh with someone!")
    async def laugh(self, ctx, member: discord.Member = None): pass

    @anime_command(name="poke", title="Poke!", help_text="Poke someone!")
    async def poke(self, ctx, member: discord.Member = None): pass

    @anime_command(name="wave", title="Wave!", help_text="Wave at someone!")
    async def wave(self, ctx, member: discord.Member = None): pass

    @anime_command(name="cry", title="Crying...", help_text="Cry with someone!")
    async def cry(self, ctx, member: discord.Member = None): pass

    @anime_command(name="dance", title="Dancing!", help_text="Dance with someone!")
    async def dance(self, ctx, member: discord.Member = None): pass

    @anime_command(name="baka", title="Baka!", help_text="Call someone baka!")
    async def baka(self, ctx, member: discord.Member = None): pass

    @anime_command(name="feed", title="Feeding!", help_text="Feed someone!")
    async def feed(self, ctx, member: discord.Member = None): pass

    @anime_command(name="bite", title="Nom!", help_text="Bite someone!")
    async def bite(self, ctx, member: discord.Member = None): pass

    @anime_command(name="blush", title="Blushing!", help_text="Blush at someone!")
    async def blush(self, ctx, member: discord.Member = None): pass

    @anime_command(name="bored", title="Bored...", help_text="Show you're bored!")
    async def bored(self, ctx, member: discord.Member = None): pass

    @anime_command(name="facepalm", title="*facepalm*", help_text="Facepalm at someone!")
    async def facepalm(self, ctx, member: discord.Member = None): pass

    @anime_command(name="cuddle", title="Cuddles!", help_text="Cuddle with someone!")
    async def cuddle(self, ctx, member: discord.Member = None): pass

    @anime_command(name="thumbsup", title="👍", help_text="Give someone a thumbs up!")
    async def thumbsup(self, ctx, member: discord.Member = None): pass

    @anime_command(name="stare", title="*stares*", help_text="Stare at someone!")
    async def stare(self, ctx, member: discord.Member = None): pass

    @anime_command(name="think", title="*thinking*", help_text="Think about someone!")
    async def think(self, ctx, member: discord.Member = None): pass

    @anime_command(name="handhold", title="Hand Holding!", help_text="Hold someone's hand!")
    async def handhold(self, ctx, member: discord.Member = None): pass

    @anime_command(name="handshake", title="Handshake!", help_text="Shake hands with someone!")
    async def handshake(self, ctx, member: discord.Member = None): pass

    @anime_command(name="punt", title="Kick!", help_text="Kick someone!")
    async def kick(self, ctx, member: discord.Member = None): pass

    @anime_command(name="lurk", title="*lurking*", help_text="Lurk at someone!")
    async def lurk(self, ctx, member: discord.Member = None): pass

    @anime_command(name="nod", title="*nods*", help_text="Nod at someone!")
    async def nod(self, ctx, member: discord.Member = None): pass

    @anime_command(name="nom", title="Nom!", help_text="Nom on someone!")
    async def nom(self, ctx, member: discord.Member = None): pass

    @anime_command(name="nope", title="Nope!", help_text="Say nope to someone!")
    async def nope(self, ctx, member: discord.Member = None): pass

    @anime_command(name="peck", title="Peck!", help_text="Give someone a peck!")
    async def peck(self, ctx, member: discord.Member = None): pass

    @anime_command(name="pout", title="*pouts*", help_text="Pout at someone!")
    async def pout(self, ctx, member: discord.Member = None): pass

    @anime_command(name="punch", title="Punch!", help_text="Punch someone!")
    async def punch(self, ctx, member: discord.Member = None): pass

    @anime_command(name="shoot", title="Bang!", help_text="Shoot at someone!")
    async def shoot(self, ctx, member: discord.Member = None): pass

    @anime_command(name="shrug", title="*shrugs*", help_text="Shrug at someone!")
    async def shrug(self, ctx, member: discord.Member = None): pass

    @anime_command(name="slap", title="Slap!", help_text="Slap someone!")
    async def slap(self, ctx, member: discord.Member = None): pass

    @anime_command(name="sleep", title="Zzz...", help_text="Fall asleep on someone!")
    async def sleep(self, ctx, member: discord.Member = None): pass

    @anime_command(name="smile", title="Smile!", help_text="Smile at someone!")
    async def smile(self, ctx, member: discord.Member = None): pass

    @anime_command(name="smug", title="*smug*", help_text="Give someone a smug look!")
    async def smug(self, ctx, member: discord.Member = None): pass

    @anime_command(name="tickle", title="Tickle!", help_text="Tickle someone!")
    async def tickle(self, ctx, member: discord.Member = None): pass

    @anime_command(name="wink", title="*winks*", help_text="Wink at someone!")
    async def wink(self, ctx, member: discord.Member = None): pass

    @anime_command(name="yawn", title="*yawns*", help_text="Yawn at someone!")
    async def yawn(self, ctx, member: discord.Member = None): pass

    @anime_command(name="yeet", title="YEET!", help_text="Yeet someone!")
    async def yeet(self, ctx, member: discord.Member = None): pass

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if not ctx.command or ctx.command.cog != self:
            return

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
            self.logger.error(f"Unexpected error in command {ctx.command}: {str(error)}")
            raise error

async def setup(bot):
    await bot.add_cog(AnimeCommands(bot))