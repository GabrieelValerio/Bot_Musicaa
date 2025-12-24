import os
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot online como {bot.user}")

async def setup_hook():
    await bot.load_extension("music")

bot.setup_hook = setup_hook
bot.run(os.getenv("DISCORD_TOKEN"))
