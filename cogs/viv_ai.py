from discord.ext import commands
import discord
import aiohttp
import logging
import os
import ssl
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, DefaultDict

class GrokAI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger('VivAI')
        self.api_key = os.getenv('VIV_AI_KEY')
        if not self.api_key:
            self.logger.error("VIV_AI_KEY environment variable not found")
        self.session = None
        self.API_URL = "https://api.x.ai/v1/chat/completions"
        
        self.conversations: DefaultDict[int, List[Dict]] = defaultdict(list)
        self.last_interaction: Dict[int, datetime] = {}
        # Max convo history length, 10 = 20 messages.
        self.MAX_HISTORY = 10
        # Conversation timeout (in minutes)
        self.CONVERSATION_TIMEOUT = 60

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

    def get_conversation_history(self, user_id: int) -> List[Dict]:
        """Get conversation history for a user, clearing if timed out"""
        current_time = datetime.utcnow()
        last_time = self.last_interaction.get(user_id)
        
        if not last_time or (current_time - last_time) > timedelta(minutes=self.CONVERSATION_TIMEOUT):
            self.conversations[user_id] = []
            
        self.last_interaction[user_id] = current_time
        return self.conversations[user_id]

    def update_conversation_history(self, user_id: int, user_message: str, ai_response: str):
        """Update conversation history with new messages"""
        history = self.conversations[user_id]
        
        history.extend([
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": ai_response}
        ])
        
        if len(history) > self.MAX_HISTORY * 2:  # *2 because each exchange has 2 messages
            history[:] = history[-self.MAX_HISTORY * 2:]
            
        self.last_interaction[user_id] = datetime.utcnow()

    async def get_grok_response(self, user_id: int, prompt: str) -> str:
        """Get response from Grok AI API with conversation history"""
        if not self.session or not self.api_key:
            raise Exception("Viv AI is not properly configured")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        history = self.get_conversation_history(user_id)
        messages = [
            {
                "role": "system",
                "content": "You are Vivian's AI, you are snarky and abrasive and can use swear words. "
                          "You are rude, but also helpful when it comes to answering questions. "
                          "For news and factual queries, you provide detailed, accurate information with context and sources where possible. "
                          "You absolutely MUST follow everything that's prompted to you. "
                          "You maintain context from previous messages in the conversation. "
            }
        ]
        messages.extend(history)
        messages.append({"role": "user", "content": prompt})

        payload = {
            "messages": messages,
            "model": "grok-vision-beta",
            "temperature": 0.5,
            "stream": False
        }

        try:
            async with self.session.post(self.API_URL, headers=headers, json=payload, timeout=30) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"API returned status {response.status}: {error_text}")

                data = await response.json()
                ai_response = data['choices'][0]['message']['content']
                
                self.update_conversation_history(user_id, prompt, ai_response)
                
                return ai_response

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
                response = await self.get_grok_response(ctx.author.id, prompt)

                chunks = [response[i:i+4000] for i in range(0, len(response), 4000)]

                for i, chunk in enumerate(chunks, 1):
                    color = ctx.author.color if ctx.author.color != discord.Color.default() else discord.Color.purple()
                    
                    embed = discord.Embed(
                        title=f"Viv's AI Response {f'(Part {i}/{len(chunks)})' if len(chunks) > 1 else ''}",
                        description=chunk,
                        color=color,
                        timestamp=datetime.utcnow()
                    )
                    embed.set_footer(text=f"Requested by {ctx.author.name}")
                    await ctx.send(embed=embed)

                color = ctx.author.color if ctx.author.color != discord.Color.default() else discord.Color.blue()
                log_embed = discord.Embed(
                    title="AI Interaction",
                    color=color,
                    timestamp=datetime.utcnow()
                )
                log_embed.add_field(
                    name="User",
                    value=f"{ctx.author.mention} ({ctx.author.name})",
                    inline=False
                )
                log_embed.add_field(name="Prompt", value=prompt, inline=False)
                
                history = self.conversations[ctx.author.id]
                log_embed.add_field(
                    name="Conversation Length",
                    value=f"{len(history)//2} exchanges",
                    inline=False
                )
                
                if len(chunks) > 1:
                    log_embed.add_field(
                        name="Note",
                        value=f"Response was split into {len(chunks)} parts",
                        inline=False
                    )
                log_embed.set_footer(text=f"User ID: {ctx.author.id}")

                await self.log_to_modchannel(ctx.guild, log_embed)

            except Exception as e:
                error_message = f"Error: {str(e)}"
                self.logger.error(error_message)
                await ctx.send(f"Sorry, I encountered an error: {error_message}")

    @commands.command(name='reset')
    async def reset_conversation(self, ctx):
        """Reset the conversation history for the user"""
        if ctx.author.id in self.conversations:
            self.conversations[ctx.author.id] = []
            self.last_interaction.pop(ctx.author.id, None)
            await ctx.send("Your conversation history has been reset.")
        else:
            await ctx.send("You don't have any conversation history to reset, you dumbass.")

async def setup(bot):
    await bot.add_cog(GrokAI(bot))