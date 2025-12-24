class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def play(self, ctx, *, query):
        await ctx.send(f"Tocando: {query}")

# ⚠️ ÚNICO setup permitido
async def setup(bot):
    await bot.add_cog(Music(bot))
