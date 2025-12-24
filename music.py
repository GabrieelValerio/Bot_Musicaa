import discord
from discord.ext import commands
import yt_dlp

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
    def __init__(self, bot):
        self.bot = bot
        self.ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

    @commands.command(name="play")
    async def play(self, ctx, *, search: str = None):
        # ❌ Usuário digitou só !play
        if search is None:
            await ctx.send("❌ Use `!play <nome ou link da música>`")
            return

        # ❌ Usuário não está em call
        if not ctx.author.voice:
            await ctx.send("❌ Você precisa estar em um canal de voz.")
            return

        channel = ctx.author.voice.channel

        # 🔊 Conectar na call
        if ctx.voice_client is None:
            vc = await channel.connect()
        else:
            vc = ctx.voice_client
            if vc.channel != channel:
                await vc.move_to(channel)

        # ⛔ Já tocando algo
        if vc.is_playing():
            await ctx.send("⚠️ Já estou tocando uma música.")
            return

        await ctx.send("🔎 Procurando música...")

        try:
            info = self.ytdl.extract_info(search, download=False)

            if "entries" in info:
                info = info["entries"][0]

            url = info["url"]
            title = info.get("title", "Música desconhecida")

            source = discord.FFmpegPCMAudio(
                url,
                **FFMPEG_OPTIONS
            )

            vc.play(source)
            await ctx.send(f"🎶 Tocando agora: **{title}**")

        except Exception as e:
            await ctx.send("❌ Erro ao tocar a música.")
            print("ERRO PLAY:", e)

    @commands.command(name="stop")
    async def stop(self, ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("⏹️ Música parada e desconectado.")
        else:
            await ctx.send("❌ Não estou em um canal de voz.")


async def setup(bot):
    await bot.add_cog(Music(bot))
