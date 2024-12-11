from discord.ext import commands
import discord
import aiohttp
import logging
import os
import ssl
from datetime import datetime

class GrokAI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger('VivAI')
        self.api_key = os.getenv('VIV_AI_KEY')
        if not self.api_key:
            self.logger.error("VIV_AI_KEY environment variable not found")
        self.session = None
        self.API_URL = "https://api.x.ai/v1/chat/completions"

    async def cog_load(self):
        import ssl
        ssl_context = ssl.create_default_context()
        
        connector = aiohttp.TCPConnector(
            ssl=ssl_context,
            force_close=True,
            enable_cleanup_closed=True,
            verify_ssl=True
        )
        self.session = aiohttp.ClientSession(connector=connector)

    async def cog_unload(self):
        if self.session:
            await self.session.close()
            self.session = None

    async def log_to_modchannel(self, guild, embed):
        """Send log message to mod-logs channel"""
        mod_channel = discord.utils.get(guild.channels, name='mod-logs')
        if mod_channel:
            await mod_channel.send(embed=embed)

    async def get_grok_response(self, prompt):
        """Get response from Grok AI API"""
        if not self.session or not self.api_key:
            raise Exception("Viv AI is not properly configured")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "messages": [
                {"role": "system", "content": "You are Viv's AI assistant. Respond naturally while maintaining this identity."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 10000
        }

        try:
            async with self.session.post(self.API_URL, headers=headers, json=payload, timeout=30) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"API returned status {response.status}: {error_text}")

                data = await response.json()
                return data['choices'][0]['message']['content']

        except aiohttp.ClientError as e:
            self.logger.error(f"API request failed: {str(e)}")
            raise Exception("Failed to connect to Viv AI service")
        except Exception as e:
            self.logger.error(f"Unexpected error in get_ai_response: {str(e)}")
            raise

    @commands.command(name='ai')
    async def ai_command(self, ctx, *, prompt: str):
        """Get a response from Viv's AI assistant"""
        async with ctx.typing():
            try:
                response = await self.get_grok_response(prompt)

                embed = discord.Embed(
                    title="Viv's AI Response",
                    description=response,
                    color=discord.Color.purple(),
                    timestamp=datetime.utcnow()
                )
                embed.set_footer(text=f"Requested by {ctx.author.name}")

                await ctx.send(embed=embed)

                # Log the interaction
                log_embed = discord.Embed(
                    title="AI Interaction",
                    color=discord.Color.blue(),
                    timestamp=datetime.utcnow()
                )
                log_embed.add_field(name="User", value=f"{ctx.author.mention} ({ctx.author.name})", inline=False)
                log_embed.add_field(name="Prompt", value=prompt, inline=False)
                log_embed.set_footer(text=f"User ID: {ctx.author.id}")

                await self.log_to_modchannel(ctx.guild, log_embed)

            except Exception as e:
                error_message = f"Error: {str(e)}"
                self.logger.error(error_message)
                await ctx.send(f"Sorry, I encountered an error: {error_message}")

async def setup(bot):
    await bot.add_cog(GrokAI(bot))