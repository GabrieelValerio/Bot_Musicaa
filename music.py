import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import asyncio
import json
import os

CONFIG_FILE = "guild_config.json"

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

guild_config = load_config()
queues = {}

def get_config(guild_id):
    gid = str(guild_id)
    if gid not in guild_config:
        guild_config[gid] = {
            "volume": 0.5,
            "loop": False,
            "stay": False
        }
        save_config(guild_config)
    return guild_config[gid]

YDL_OPTIONS = {
    "format": "bestaudio/best",
    "quiet": True,
    "default_search": "ytsearch",
    "noplaylist": True
}

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn"
}

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def play_next(self, guild):
        if guild.id not in queues or not queues[guild.id]:
            if not get_config(guild.id)["stay"]:
                vc = guild.voice_client
                if vc:
                    await vc.disconnect()
            return

        vc = guild.voice_client
        if not vc:
            return

        url = queues[guild.id][0]
        config = get_config(guild.id)

        def after_play(error):
            if not config["loop"]:
                queues[guild.id].pop(0)

            fut = self.play_next(guild)
            asyncio.run_coroutine_threadsafe(fut, self.bot.loop)

        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_url = info["url"]

        source = discord.FFmpegPCMAudio(audio_url, **FFMPEG_OPTIONS)
        vc.play(
            discord.PCMVolumeTransformer(source, volume=config["volume"]),
            after=after_play
        )

    @app_commands.command(name="play", description="Tocar música do YouTube")
    async def play(self, interaction: discord.Interaction, busca: str):
        await interaction.response.defer()

        if not interaction.user.voice:
            await interaction.followup.send("❌ Entre em um canal de voz.")
            return

        vc = interaction.guild.voice_client
        if not vc:
            vc = await interaction.user.voice.channel.connect()

        queues.setdefault(interaction.guild.id, [])

        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(busca, download=False)
            if "entries" in info:
                url = info["entries"][0]["url"]
            else:
                url = info["url"]

        queues[interaction.guild.id].append(url)

        if not vc.is_playing():
            await self.play_next(interaction.guild)

        await interaction.followup.send("🎶 Música adicionada à fila")

    @app_commands.command(name="pause")
    async def pause(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc and vc.is_playing():
            vc.pause()
            await interaction.response.send_message("⏸️ Pausado")

    @app_commands.command(name="resume")
    async def resume(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc and vc.is_paused():
            vc.resume()
            await interaction.response.send_message("▶️ Retomado")

    @app_commands.command(name="leave")
    async def leave(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc:
            queues.pop(interaction.guild.id, None)
            await vc.disconnect()
            await interaction.response.send_message("👋 Saí do canal")

    @app_commands.command(name="loop")
    async def loop(self, interaction: discord.Interaction):
        config = get_config(interaction.guild.id)
        config["loop"] = not config["loop"]
        save_config(guild_config)
        await interaction.response.send_message(f"🔁 Loop: {config['loop']}")

    @app_commands.command(name="247")
    async def stay(self, interaction: discord.Interaction):
        config = get_config(interaction.guild.id)
        config["stay"] = not config["stay"]
        save_config(guild_config)
        await interaction.response.send_message(f"🔒 24/7: {config['stay']}")

    @app_commands.command(name="volume")
    async def volume(self, interaction: discord.Interaction, valor: int):
        if not 0 <= valor <= 100:
            await interaction.response.send_message("❌ Volume entre 0 e 100")
            return
        config = get_config(interaction.guild.id)
        config["volume"] = valor / 100
        save_config(guild_config)
        await interaction.response.send_message(f"🔊 Volume definido para {valor}%")

async def setup(bot):
    await bot.add_cog(Music(bot))
