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

ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="play")
    async def play(self, ctx, *, search: str = None):
        if not search:
            await ctx.send("❌ Use: `!play nome_da_musica`")
            return

        if not ctx.author.voice:
            await ctx.send("❌ Você precisa estar em um canal de voz.")
            return

        voice_channel = ctx.author.voice.channel

        if ctx.voice_client:
            await ctx.voice_client.move_to(voice_channel)
        else:
            await voice_channel.connect()

        await ctx.send("🔎 Procurando música...")

        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(
            None, lambda: ytdl.extract_info(search, download=False)
        )

        if "entries" in data:
            data = data["entries"][0]

        if not data or "url" not in data:
            await ctx.send("❌ Não consegui encontrar essa música.")
            return

        url = data["url"]
        title = data.get("title", "Música desconhecida")

        source = discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS)

        ctx.voice_client.play(
            source,
            after=lambda e: print(f"Erro no player: {e}") if e else None,
        )

        await ctx.send(f"🎶 Tocando agora: **{title}**")

    @commands.command(name="stop")
    async def stop(self, ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("⏹️ Música parada e bot desconectado.")


async def setup(bot):
    await bot.add_cog(Music(bot))
