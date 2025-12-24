import discord
from discord.ext import commands
import os

intents = discord.Intents.default()

class Bot(commands.Bot):
    async def setup_hook(self):
        await self.load_extension("music")
        await self.tree.sync()
        print("✅ Slash commands sincronizados")

bot = Bot(command_prefix="!", intents=intents)

bot.run(os.getenv("DISCORD_TOKEN"))
