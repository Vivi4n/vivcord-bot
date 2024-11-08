from discord.ext import commands
from discord import app_commands
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

    async def _fetch_anime_image(self, interaction: discord.Interaction, api_url: str, title: str):
        try:
            await interaction.response.defer()

            async with self.session.get(api_url) as response:
                if response.status == 200:
                    data = await response.json()
                    image_url = data.get('url')

                    if not image_url:
                        await interaction.followup.send(
                            "Sorry, couldn't find an image right now. Try again later!"
                        )
                        return

                    embed = discord.Embed(
                        title=title,
                        color=discord.Color.purple(),
                        timestamp=datetime.utcnow()
                    )
                    embed.set_image(url=image_url)
                    embed.set_footer(text="Powered by waifu.pics | SFW Content Only")

                    await interaction.followup.send(embed=embed)
                else:
                    await interaction.followup.send(
                        "Sorry, there was an error accessing the anime image service."
                    )

        except Exception as e:
            self.logger.error(f"Unexpected error in anime command: {str(e)}")
            await interaction.followup.send(
                "An unexpected error occurred. Please try again later."
            )

    waifu = app_commands.command(
        name="waifu",
        description="Get a random SFW anime character image"
    )(waifu)

    husbando = app_commands.command(
        name="husbando",
        description="Get a random SFW male anime character image"
    )(husbando)

async def setup(bot):
    # First, remove any existing commands
    bot.tree.clear_commands(guild=None)
    await bot.tree.sync()
    
    # Now add our cog
    await bot.add_cog(AnimeCommands(bot))
    
    # Sync the new commands
    await bot.tree.sync()
    
    print("Anime commands have been registered!")