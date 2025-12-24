import discord
from discord.ext import commands
import yt_dlp

YDL_OPTIONS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "default_search": "ytsearch",
}

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn"
}


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="play")
    async def play(self, ctx, *, search: str = None):
        # ❌ usuário não digitou nada
        if not search:
            return await ctx.send("❌ Você precisa informar um link ou nome da música.\nEx: `!play link`")

        # ❌ usuário não está em call
        if not ctx.author.voice:
            return await ctx.send("❌ Você precisa estar em um canal de voz.")

        voice_channel = ctx.author.voice.channel

        # conecta na call
        if not ctx.voice_client:
            vc = await voice_channel.connect()
        else:
            vc = ctx.voice_client

        await ctx.send("🔍 Procurando música...")

        try:
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(search, download=False)

                # se for pesquisa
                if "entries" in info:
                    info = info["entries"][0]

                url = info.get("url")
                title = info.get("title")

                if not url:
                    return await ctx.send("❌ Não consegui obter o áudio desse vídeo.")

        except Exception as e:
            print("YT-DLP ERROR:", e)
            return await ctx.send("❌ Erro ao buscar a música.")

        try:
            source = discord.FFmpegPCMAudio(
                url,
                executable="ffmpeg",
                **FFMPEG_OPTIONS
            )

            vc.stop()
            vc.play(source)

            await ctx.send(f"🎶 Tocando agora: **{title}**")

        except Exception as e:
            print("FFMPEG ERROR:", e)
            await ctx.send("❌ Erro ao tocar a música.")

    @commands.command(name="stop")
    async def stop(self, ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("⏹️ Música parada e bot desconectado.")


async def setup(bot):
    await bot.add_cog(Music(bot))
