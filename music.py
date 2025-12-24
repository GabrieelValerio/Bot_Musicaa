import discord
from discord.ext import commands
import yt_dlp
import asyncio

YTDL_OPTIONS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "default_search": "ytsearch",
}

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def ensure_voice(self, ctx):
        if ctx.author.voice is None:
            await ctx.send("❌ Você precisa estar em um canal de voz.")
            return False

        if ctx.voice_client is None:
            await ctx.author.voice.channel.connect()
        elif ctx.voice_client.channel != ctx.author.voice.channel:
            await ctx.voice_client.move_to(ctx.author.voice.channel)

        return True

    @commands.command(name="play")
    async def play(self, ctx, *, search: str):
        if not await self.ensure_voice(ctx):
            return

        await ctx.send(f"🔎 Procurando: **{search}**")

        loop = asyncio.get_event_loop()

        def extract():
            with yt_dlp.YoutubeDL(YTDL_OPTIONS) as ytdl:
                return ytdl.extract_info(search, download=False)

        info = await loop.run_in_executor(None, extract)

        if "entries" in info:
            info = info["entries"][0]

        url = info["url"]
        title = info.get("title", "Desconhecido")

        source = discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS)

        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()

        ctx.voice_client.play(source)

        await ctx.send(f"🎶 Tocando agora: **{title}**")

    @commands.command(name="stop")
    async def stop(self, ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("⏹️ Música parada e desconectado.")


# ⚠️ OBRIGATÓRIO para discord.py 2.x
async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))
