import discord
from discord.ext import commands
import os
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

class Bot(commands.Bot):
    async def setup_hook(self):
        await self.load_extension("music")
        await self.tree.sync()

bot = Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening,
            name="Pensando na morte do Kazunari Nara 😍"
        )
    )
    print(f"✅ Bot online como {bot.user}")

bot.run(os.getenv("DISCORD_TOKEN"))
