import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import asyncio
import re

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn"
}

YTDL_OPTIONS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "default_search": "ytsearch",
}

ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

queues = {}
loops = {}

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_audio(self, query):
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(
            None,
            lambda: ytdl.extract_info(query, download=False)
        )

        if "entries" in data:
            data = data["entries"][0]

        return data["url"], data["title"]

    async def play_next(self, guild):
        if loops.get(guild.id) and queues[guild.id]:
            url, title = queues[guild.id][0]
        elif queues[guild.id]:
            queues[guild.id].pop(0)
            if not queues[guild.id]:
                return
            url, title = queues[guild.id][0]
        else:
            return

        source = discord.PCMVolumeTransformer(
            discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS),
            volume=0.5
        )

        guild.voice_client.play(
            source,
            after=lambda e: asyncio.run_coroutine_threadsafe(
                self.play_next(guild),
                self.bot.loop
            )
        )

    def spotify_to_search(self, url):
        match = re.search(r"track/([A-Za-z0-9]+)", url)
        if not match:
            return None
        return f"spotify song {match.group(1)}"

    @app_commands.command(name="play", description="Toca uma música (YouTube ou Spotify)")
    async def play(self, interaction: discord.Interaction, search: str):
        await interaction.response.defer()

        if not interaction.user.voice:
            await interaction.followup.send("❌ Entre em um canal de voz.")
            return

        vc = interaction.guild.voice_client
        if not vc:
            vc = await interaction.user.voice.channel.connect()

        if interaction.guild.id not in queues:
            queues[interaction.guild.id] = []
            loops[interaction.guild.id] = False

        if "spotify.com" in search:
            search = search.replace("https://open.spotify.com/", "")

        url, title = await self.get_audio(search)
        queues[interaction.guild.id].append((url, title))

        await interaction.followup.send(f"🎶 **Adicionado à fila:** {title}")

        if not vc.is_playing():
            await self.play_next(interaction.guild)

    @app_commands.command(name="skip", description="Pula a música atual")
    async def skip(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc and vc.is_playing():
            vc.stop()
            await interaction.response.send_message("⏭️ Música pulada.")
        else:
            await interaction.response.send_message("❌ Nada tocando.")

    @app_commands.command(name="stop", description="Para a música e limpa a fila")
    async def stop(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc:
            queues[interaction.guild.id] = []
            loops[interaction.guild.id] = False
            await vc.disconnect()
            await interaction.response.send_message("⏹️ Música parada.")
        else:
            await interaction.response.send_message("❌ Não estou em call.")

    @app_commands.command(name="loop", description="Ativa ou desativa loop")
    async def loop(self, interaction: discord.Interaction):
        gid = interaction.guild.id
        loops[gid] = not loops.get(gid, False)
        await interaction.response.send_message(
            "🔁 Loop ativado" if loops[gid] else "⏹️ Loop desativado"
        )

    @app_commands.command(name="volume", description="Define o volume (0-100)")
    async def volume(self, interaction: discord.Interaction, level: int):
        vc = interaction.guild.voice_client
        if not vc or not vc.source:
            await interaction.response.send_message("❌ Nada tocando.")
            return

        if level < 0 or level > 100:
            await interaction.response.send_message("❌ Use 0 a 100.")
            return

        vc.source.volume = level / 100
        await interaction.response.send_message(f"🔊 Volume: {level}%")

    @app_commands.command(name="help", description="Mostra os comandos")
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎵 Comandos do Bot",
            color=discord.Color.blue()
        )

        embed.add_field(name="/play", value="Toca música do YouTube ou Spotify", inline=False)
        embed.add_field(name="/skip", value="Pula a música", inline=False)
        embed.add_field(name="/stop", value="Para tudo", inline=False)
        embed.add_field(name="/loop", value="Liga/desliga loop", inline=False)
        embed.add_field(name="/volume", value="Define volume", inline=False)

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Music(bot))
