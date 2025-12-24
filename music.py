import discord
from discord.ext import commands
import yt_dlp
import asyncio

ytdlp_opts = {
    "format": "bestaudio/best",
    "quiet": True,
    "default_search": "ytsearch",
    "noplaylist": True
}

ffmpeg_opts = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn"
}

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = {}

    def get_queue(self, guild_id):
        return self.queue.setdefault(guild_id, [])

    async def play_next(self, ctx):
        queue = self.get_queue(ctx.guild.id)
        if not queue:
            return

        url, title = queue.pop(0)
        source = await discord.FFmpegOpusAudio.from_probe(url, **ffmpeg_opts)

        ctx.voice_client.play(
            source,
            after=lambda e: asyncio.run_coroutine_threadsafe(
                self.play_next(ctx), self.bot.loop
            )
        )

        await ctx.send(f"🎶 Tocando agora: **{title}**")

    @commands.command()
    async def play(self, ctx, *, query):
        if not ctx.author.voice:
            return await ctx.send("❌ Entre em um canal de voz.")

        if not ctx.voice_client:
            await ctx.author.voice.channel.connect()

        with yt_dlp.YoutubeDL(ytdlp_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            if "entries" in info:
                info = info["entries"][0]

        url = info["url"]
        title = info["title"]

        queue = self.get_queue(ctx.guild.id)
        queue.append((url, title))

        if not ctx.voice_client.is_playing():
            await self.play_next(ctx)
        else:
            await ctx.send(f"➕ Adicionado à fila: **{title}**")

    @commands.command()
    async def skip(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("⏭️ Pulado.")

    @commands.command()
    async def stop(self, ctx):
        if ctx.voice_client:
            self.queue[ctx.guild.id] = []
            await ctx.voice_client.disconnect()
            await ctx.send("⏹️ Desconectado.")

def setup(bot):
    bot.add_cog(Music(bot))
