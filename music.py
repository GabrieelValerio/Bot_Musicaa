import discord
from discord.ext import commands
import yt_dlp
import asyncio

# =====================
# CONFIGURAÇÕES
# =====================

YTDL_OPTIONS = {
    "format": "bestaudio[ext=m4a]/bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "default_search": "ytsearch",
    "source_address": "0.0.0.0",
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
            await ctx.send("❌ Uso correto: `!play nome_da_musica_ou_link`")
            return

        if not ctx.author.voice:
            await ctx.send("❌ Você precisa estar em um canal de voz.")
            return

        channel = ctx.author.voice.channel

        if ctx.voice_client:
            await ctx.voice_client.move_to(channel)
        else:
            await channel.connect()

        await ctx.send("🔎 Procurando a música...")

        loop = asyncio.get_event_loop()
        try:
            info = await loop.run_in_executor(
                None, lambda: ytdl.extract_info(search, download=False)
            )
        except Exception as e:
            await ctx.send("❌ Erro ao buscar a música.")
            print(e)
            return

        if "entries" in info:
            info = info["entries"][0]

        if not info or "url" not in info:
            await ctx.send("❌ Não encontrei nenhuma música.")
            return

        url = info["url"]
        title = info.get("title", "Música desconhecida")

        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()

        try:
            source = discord.FFmpegPCMAudio(
                url,
                executable="/usr/bin/ffmpeg",
                **FFMPEG_OPTIONS
            )
        except Exception as e:
            await ctx.send("❌ Falha ao criar o player de áudio.")
            print("FFMPEG ERROR:", e)
            return

        ctx.voice_client.play(
            source,
            after=lambda e: print(f"Erro no áudio: {e}") if e else None
        )

        await ctx.send(f"🎶 Tocando agora: **{title}**")

    @commands.command()
    async def stop(self, ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("⏹️ Bot desconectado.")
        else:
            await ctx.send("❌ O bot não está em call.")


async def setup(bot):
    await bot.add_cog(Music(bot))
