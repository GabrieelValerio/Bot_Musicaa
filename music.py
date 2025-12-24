import discord
from discord.ext import commands
import yt_dlp
import asyncio

YDL_OPTIONS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
}

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn"
}

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = []
        self.is_playing = False
        self.voice_client: discord.VoiceClient | None = None
        self.stay_247 = True  # modo 24/7

    # ========================
    # 🔊 PLAY
    # ========================
    @commands.command(name="play")
    async def play(self, ctx, *, search: str = None):
        if search is None:
            await ctx.send("❌ Use: `!play <nome ou link>`")
            return

        if not ctx.author.voice:
            await ctx.send("❌ Você precisa estar em um canal de voz.")
            return

        channel = ctx.author.voice.channel

        if self.voice_client is None or not self.voice_client.is_connected():
            self.voice_client = await channel.connect(reconnect=True)

        # adiciona à fila
        self.queue.append(search)
        await ctx.send(f"🎶 Adicionado à fila: **{search}**")

        if not self.is_playing:
            await self.play_next(ctx)

    # ========================
    # ▶️ TOCAR PRÓXIMA
    # ========================
    async def play_next(self, ctx):
        if len(self.queue) == 0:
            self.is_playing = False
            if not self.stay_247 and self.voice_client:
                await self.voice_client.disconnect()
            return

        self.is_playing = True
        search = self.queue.pop(0)

        def get_audio():
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(search, download=False)
                if "entries" in info:
                    info = info["entries"][0]
                return info["url"], info.get("title", "Música")

        try:
            url, title = await asyncio.to_thread(get_audio)
            source = discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS)

            self.voice_client.play(
                source,
                after=lambda e: asyncio.run_coroutine_threadsafe(
                    self.play_next(ctx), self.bot.loop
                )
            )

            await ctx.send(f"▶️ Tocando agora: **{title}**")

        except Exception as e:
            await ctx.send("❌ Erro ao tocar a música.")
            print("ERRO PLAY:", e)
            await self.play_next(ctx)

    # ========================
    # ⏭️ SKIP
    # ========================
    @commands.command(name="skip")
    async def skip(self, ctx):
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.stop()
            await ctx.send("⏭️ Música pulada.")
        else:
            await ctx.send("❌ Nada tocando.")

    # ========================
    # ⏹️ STOP
    # ========================
    @commands.command(name="stop")
    async def stop(self, ctx):
        self.queue.clear()
        if self.voice_client:
            self.voice_client.stop()
        await ctx.send("⏹️ Música parada e fila limpa.")

    # ========================
    # ⏸️ PAUSE
    # ========================
    @commands.command(name="pause")
    async def pause(self, ctx):
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.pause()
            await ctx.send("⏸️ Pausado.")
        else:
            await ctx.send("❌ Nada tocando.")

    # ========================
    # ▶️ RESUME
    # ========================
    @commands.command(name="resume")
    async def resume(self, ctx):
        if self.voice_client and self.voice_client.is_paused():
            self.voice_client.resume()
            await ctx.send("▶️ Continuando.")
        else:
            await ctx.send("❌ Nada pausado.")

    # ========================
    # 🔁 24/7
    # ========================
    @commands.command(name="247")
    async def toggle_247(self, ctx):
        self.stay_247 = not self.stay_247
        status = "ATIVADO" if self.stay_247 else "DESATIVADO"
        await ctx.send(f"🔁 Modo 24/7 {status}.")

# ========================
# SETUP
# ========================
async def setup(bot):
    await bot.add_cog(Music(bot))
