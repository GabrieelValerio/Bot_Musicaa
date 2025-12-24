import discord
from discord.ext import commands
from discord import app_commands
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
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.loop = False
        self.current = None

    async def play_source(self, interaction: discord.Interaction, url: str):
        vc = interaction.guild.voice_client

        if not vc:
            return

        def after_play(error):
            if error:
                print("Erro no player:", error)
            if self.loop:
                fut = asyncio.run_coroutine_threadsafe(
                    self.play_source(interaction, self.current),
                    self.bot.loop
                )
                fut.result()

        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_url = info["url"]
            title = info["title"]

        self.current = url

        source = discord.FFmpegPCMAudio(audio_url, **FFMPEG_OPTIONS)
        vc.play(source, after=after_play)

        await interaction.followup.send(f"🎶 **Tocando:** {title}")

    # ---------- SLASH COMMANDS ----------

    @app_commands.command(name="play", description="Tocar música do YouTube")
    async def play(self, interaction: discord.Interaction, busca: str = None):
        if not busca:
            await interaction.response.send_message(
                "❌ Você precisa informar um link ou nome da música.",
                ephemeral=True
            )
            return

        if not interaction.user.voice:
            await interaction.response.send_message(
                "❌ Você precisa estar em um canal de voz.",
                ephemeral=True
            )
            return

        await interaction.response.defer()

        vc = interaction.guild.voice_client
        if not vc:
            vc = await interaction.user.voice.channel.connect()

        await self.play_source(interaction, busca)

    @app_commands.command(name="pause", description="Pausar a música")
    async def pause(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc and vc.is_playing():
            vc.pause()
            await interaction.response.send_message("⏸ Música pausada.")
        else:
            await interaction.response.send_message("❌ Nada tocando.", ephemeral=True)

    @app_commands.command(name="resume", description="Retomar a música")
    async def resume(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc and vc.is_paused():
            vc.resume()
            await interaction.response.send_message("▶ Música retomada.")
        else:
            await interaction.response.send_message("❌ A música não está pausada.", ephemeral=True)

    @app_commands.command(name="loop", description="Ativar/desativar loop")
    async def loop_cmd(self, interaction: discord.Interaction):
        self.loop = not self.loop
        status = "ativado 🔁" if self.loop else "desativado ❌"
        await interaction.response.send_message(f"Loop {status}.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))
