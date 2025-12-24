import discord
from discord.ext import commands
import yt_dlp
import asyncio

# =====================
# CONFIGURAÇÕES
# =====================

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


# =====================
# COG DE MÚSICA
# =====================

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # -----------------
    # !play
    # -----------------
    @commands.command(name="play")
    async def play(self, ctx, *, search: str = None):

        # ❌ Usuário não passou nada
        if not search:
            await ctx.send("❌ Uso correto: `!play nome_da_musica_ou_link`")
            return

        # ❌ Usuário não está em call
        if not ctx.author.voice:
            await ctx.send("❌ Você precisa estar em um canal de voz.")
            return

        voice_channel = ctx.author.voice.channel

        # 🔊 Conecta ou move o bot
        if ctx.voice_client:
            await ctx.voice_client.move_to(voice_channel)
        else:
            await voice_channel.connect()

        await ctx.send("🔎 Procurando a música...")

        # 🔍 Busca no YouTube (thread separada)
        loop = asyncio.get_event_loop()
        try:
            data = await loop.run_in_executor(
                None, lambda: ytdl.extract_info(search, download=False)
            )
        except Exception:
            await ctx.send("❌ Erro ao buscar a música.")
            return

        # 🎯 Pega o primeiro resultado
        if "entries" in data:
            data = data["entries"][0]

        if not data or "url" not in data:
            await ctx.send("❌ Não encontrei nenhuma música com esse nome.")
            return

        url = data["url"]
        title = data.get("title", "Música desconhecida")

        # ⏹️ Para música atual (se houver)
        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()

        # 🎶 Cria o player
        try:
            source = discord.FFmpegPCMAudio(
                url,
                executable="ffmpeg",
                **FFMPEG_OPTIONS
            )
        except Exception:
            await ctx.send("❌ Erro ao iniciar o player de áudio.")
            return

        ctx.voice_client.play(
            source,
            after=lambda e: print(f"Erro no player: {e}") if e else None
        )

        await ctx.send(f"🎶 Tocando agora: **{title}**")

    # -----------------
    # !stop
    # -----------------
    @commands.command(name="stop")
    async def stop(self, ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("⏹️ Música parada e bot desconectado.")
        else:
            await ctx.send("❌ O bot não está em um canal de voz.")

    # -----------------
    # !pause
    # -----------------
    @commands.command(name="pause")
    async def pause(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send("⏸️ Música pausada.")
        else:
            await ctx.send("❌ Nenhuma música tocando.")

    # -----------------
    # !resume
    # -----------------
    @commands.command(name="resume")
    async def resume(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send("▶️ Música retomada.")
        else:
            await ctx.send("❌ A música não está pausada.")


# =====================
# SETUP DO COG
# =====================

async def setup(bot):
    await bot.add_cog(Music(bot))
