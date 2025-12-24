import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from music import Music

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot online como {bot.user}")

bot.add_cog(Music(bot))

bot.run(os.getenv("DISCORD_TOKEN"))

