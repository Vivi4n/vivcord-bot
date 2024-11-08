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
        self.husbando_api_url = "https://nekos.best/api/v2/husbando"
        self.session = None

    async def cog_load(self):
        """Create aiohttp session when cog loads"""
        self.session = aiohttp.ClientSession()

    async def cog_unload(self):
        """Close aiohttp session when cog unloads"""
        if self.session:
            await self.session.close()

    async def _fetch_waifu_image(self, interaction: discord.Interaction):
        """Helper method to fetch waifu images from waifu.pics API"""
        try:
            await interaction.response.defer()

            async with self.session.get(self.waifu_api_url) as response:
                if response.status == 200:
                    data = await response.json()
                    image_url = data.get('url')

                    if not image_url:
                        await interaction.followup.send(
                            "Sorry, couldn't find an image right now. Try again later!"
                        )
                        return

                    embed = discord.Embed(
                        title="Random Anime Character",
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

        except aiohttp.ClientError as e:
            self.logger.error(f"API request failed: {str(e)}")
            await interaction.followup.send(
                "Sorry, there was an error connecting to the anime image service."
            )
        except Exception as e:
            self.logger.error(f"Unexpected error in waifu command: {str(e)}")
            await interaction.followup.send(
                "An unexpected error occurred. Please try again later."
            )

    async def _fetch_husbando_image(self, interaction: discord.Interaction):
        """Helper method to fetch husbando images from nekos.best API"""
        try:
            await interaction.response.defer()

            async with self.session.get(self.husbando_api_url) as response:
                if response.status == 200:
                    data = await response.json()
                    # Nekos.best API returns results in a different format
                    image_url = data.get('results', [{}])[0].get('url')
                    artist_name = data.get('results', [{}])[0].get('artist_name')

                    if not image_url:
                        await interaction.followup.send(
                            "Sorry, couldn't find an image right now. Try again later!"
                        )
                        return

                    embed = discord.Embed(
                        title="Random Male Anime Character",
                        color=discord.Color.purple(),
                        timestamp=datetime.utcnow()
                    )
                    embed.set_image(url=image_url)
                    footer_text = "Powered by nekos.best | SFW Content Only"
                    if artist_name:
                        footer_text = f"Art by {artist_name} | " + footer_text
                    embed.set_footer(text=footer_text)

                    await interaction.followup.send(embed=embed)
                else:
                    await interaction.followup.send(
                        "Sorry, there was an error accessing the anime image service."
                    )

        except aiohttp.ClientError as e:
            self.logger.error(f"API request failed: {str(e)}")
            await interaction.followup.send(
                "Sorry, there was an error connecting to the anime image service."
            )
        except Exception as e:
            self.logger.error(f"Unexpected error in husbando command: {str(e)}")
            await interaction.followup.send(
                "An unexpected error occurred. Please try again later."
            )

    @app_commands.command(
        name="waifu",
        description="Get a random SFW anime character image"
    )
    @app_commands.checks.cooldown(1, 5.0)  # 1 use per 5 seconds per user
    async def waifu(self, interaction: discord.Interaction):
        """Get a random SFW anime character image"""
        await self._fetch_waifu_image(interaction)

    @app_commands.command(
        name="husbando",
        description="Get a random SFW male anime character image"
    )
    @app_commands.checks.cooldown(1, 5.0)  # 1 use per 5 seconds per user
    async def husbando(self, interaction: discord.Interaction):
        """Get a random SFW male anime character image"""
        await self._fetch_husbando_image(interaction)

    @waifu.error
    @husbando.error
    async def anime_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Error handler for the anime commands"""
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(
                f"Please wait {error.retry_after:.1f} seconds before using this command again!",
                ephemeral=True
            )
        else:
            self.logger.error(f"Unhandled error in anime command: {str(error)}")
            await interaction.response.send_message(
                "An error occurred while processing your request.",
                ephemeral=True
            )

async def setup(bot):
    # Install required package if not already installed
    try:
        import aiohttp
    except ImportError:
        import subprocess
        subprocess.check_call(["pip", "install", "aiohttp"])
    
    anime_cog = AnimeCommands(bot)
    await bot.add_cog(anime_cog)
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")