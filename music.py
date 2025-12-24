import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import asyncio

YDL_OPTIONS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True
}

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn"
}

class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.queue = []
        self.voice_client: discord.VoiceClient | None = None
        self.is_playing = False
        self.stay_247 = True

    # ======================
    # 🎵 PLAY
    # ======================
    @app_commands.command(name="play", description="Tocar música do YouTube")
    @app_commands.describe(search="Nome ou link da música")
    async def play(self, interaction: discord.Interaction, search: str):
        await interaction.response.defer()

        if not interaction.user.voice:
            await interaction.followup.send("❌ Você precisa estar em um canal de voz.")
            return

        channel = interaction.user.voice.channel

        if self.voice_client is None or not self.voice_client.is_connected():
            self.voice_client = await channel.connect(reconnect=True)

        self.queue.append(search)
        await interaction.followup.send(f"🎶 Adicionado à fila: **{search}**")

        if not self.is_playing:
            await self.play_next(interaction)

    # ======================
    # ▶️ PLAY NEXT
    # ======================
    async def play_next(self, interaction: discord.Interaction):
        if len(self.queue) == 0:
            self.is_playing = False
            if not self.stay_247 and self.voice_client:
                await self.voice_client.disconnect()
            return

        self.is_playing = True
        search = self.queue.pop(0)

        def get_audio():
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                if not search.startswith("http"):
                    search_query = f"ytsearch:1:{search}"
                else:
                    search_query = search

                info = ydl.extract_info(search_query, download=False)

                if "entries" in info:
                    info = info["entries"][0]

                return info["url"], info.get("title", "Música")


        try:
            url, title = await asyncio.to_thread(get_audio)
            source = discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS)

            self.voice_client.play(
                source,
                after=lambda e: asyncio.run_coroutine_threadsafe(
                    self.play_next(interaction), self.bot.loop
                )
            )

            await interaction.followup.send(f"▶️ Tocando agora: **{title}**")

        except Exception as e:
            print("ERRO PLAY:", e)
            await interaction.followup.send("❌ Erro ao tocar a música.")
            await self.play_next(interaction)

    # ======================
    # ⏭️ SKIP
    # ======================
    @app_commands.command(name="skip", description="Pular música atual")
    async def skip(self, interaction: discord.Interaction):
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.stop()
            await interaction.response.send_message("⏭️ Música pulada.")
        else:
            await interaction.response.send_message("❌ Nada tocando.")

    # ======================
    # ⏸️ PAUSE
    # ======================
    @app_commands.command(name="pause", description="Pausar música")
    async def pause(self, interaction: discord.Interaction):
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.pause()
            await interaction.response.send_message("⏸️ Pausado.")
        else:
            await interaction.response.send_message("❌ Nada tocando.")

    # ======================
    # ▶️ RESUME
    # ======================
    @app_commands.command(name="resume", description="Continuar música")
    async def resume(self, interaction: discord.Interaction):
        if self.voice_client and self.voice_client.is_paused():
            self.voice_client.resume()
            await interaction.response.send_message("▶️ Continuando.")
        else:
            await interaction.response.send_message("❌ Nada pausado.")

    # ======================
    # ⏹️ STOP
    # ======================
    @app_commands.command(name="stop", description="Parar música e limpar fila")
    async def stop(self, interaction: discord.Interaction):
        self.queue.clear()
        if self.voice_client:
            self.voice_client.stop()
        await interaction.response.send_message("⏹️ Música parada e fila limpa.")

    # ======================
    # 📜 QUEUE
    # ======================
    @app_commands.command(name="queue", description="Ver fila de músicas")
    async def queue_cmd(self, interaction: discord.Interaction):
        if not self.queue:
            await interaction.response.send_message("📭 Fila vazia.")
            return

        text = "\n".join(f"{i+1}. {m}" for i, m in enumerate(self.queue))
        await interaction.response.send_message(f"📜 **Fila:**\n{text}")

    # ======================
    # 🔁 24/7
    # ======================
    @app_commands.command(name="247", description="Ativar/desativar modo 24/7")
    async def toggle_247(self, interaction: discord.Interaction):
        self.stay_247 = not self.stay_247
        status = "ATIVADO" if self.stay_247 else "DESATIVADO"
        await interaction.response.send_message(f"🔁 Modo 24/7 {status}")

# ======================
# SETUP
# ======================
async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))
