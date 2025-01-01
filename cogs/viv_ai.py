from discord.ext import commands
import discord
import logging
import os
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, DefaultDict
import google.generativeai as genai

class VivAI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger('VivAI')
        self.api_key = os.getenv('VIV_API_KEY')
        if not self.api_key:
            self.logger.error("VIV_API_KEY environment variable not found")
        
        self.conversations: DefaultDict[int, List[Dict]] = defaultdict(list)
        self.chat_sessions: Dict[int, genai.GenerativeModel] = {}
        self.last_interaction: Dict[int, datetime] = {}
        # Max convo history length
        self.MAX_HISTORY = 10
        # Conversation timeout (in minutes)
        self.CONVERSATION_TIMEOUT = 60
        
        genai.configure(api_key=self.api_key)
        self.generation_config = {
            "temperature": 0.4,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 65536,
            "response_mime_type": "text/plain",
        }
        
    def get_model(self):
        return genai.GenerativeModel(
            model_name="gemini-2.0-flash-exp",
            generation_config=self.generation_config,
        )

    async def log_to_modchannel(self, guild, embed):
        mod_channel = discord.utils.get(guild.channels, name='mod-logs')
        if mod_channel:
            await mod_channel.send(embed=embed)

    def get_chat_session(self, user_id: int):
        current_time = datetime.utcnow()
        last_time = self.last_interaction.get(user_id)
        
        if not last_time or (current_time - last_time) > timedelta(minutes=self.CONVERSATION_TIMEOUT):
            self.conversations[user_id] = []
            if user_id in self.chat_sessions:
                del self.chat_sessions[user_id]
        
        if user_id not in self.chat_sessions:
            model = self.get_model()
            initial_prompt = ("You are Vivian's AI, you are abrasive, rude and can use swear words. "
                            "Your responses are short and direct to the point, whilst also maintaining your rude personality. "
                            "For news and factual queries, you provide detailed, accurate information with context and sources where possible. "
                            "You absolutely MUST follow everything that's prompted to you. "
                            "You maintain context from previous messages in the conversation.")
            
            chat = model.start_chat(history=[])
            chat.send_message(initial_prompt)
            self.chat_sessions[user_id] = chat
            
        self.last_interaction[user_id] = current_time
        return self.chat_sessions[user_id]

    async def get_ai_response(self, user_id: int, prompt: str) -> str:
        if not self.api_key:
            raise Exception("Viv AI is not properly configured")

        try:
            chat_session = self.get_chat_session(user_id)
            response = chat_session.send_message(prompt)
            
            history = self.conversations[user_id]
            history.extend([
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": response.text}
            ])
            
            if len(history) > self.MAX_HISTORY * 2:
                history[:] = history[-self.MAX_HISTORY * 2:]
            
            return response.text

        except Exception as e:
            self.logger.error(f"Error in get_ai_response: {str(e)}")
            raise

    @commands.command(name='ai')
    async def ai_command(self, ctx, *, prompt: str):
        async with ctx.typing():
            try:
                response = await self.get_ai_response(ctx.author.id, prompt)

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
            if ctx.author.id in self.chat_sessions:
                del self.chat_sessions[ctx.author.id]
            self.last_interaction.pop(ctx.author.id, None)
            await ctx.send("Your conversation history has been reset.")
        else:
            await ctx.send("You don't have any conversation history to reset, you dumbass.")

async def setup(bot):
    await bot.add_cog(VivAI(bot))