import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import asyncio
import json
import os

CONFIG_FILE = "guild_config.json"

# ================= CONFIG =================

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

# ================= YTDLP =================

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

# ================= COG =================

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def play_next(self, guild):
        vc = guild.voice_client
        if not vc:
            return

        if guild.id not in queues or not queues[guild.id]:
            if not get_config(guild.id)["stay"]:
                await vc.disconnect()
            return

        config = get_config(guild.id)
        url = queues[guild.id][0]

        def after_play(error):
            if error:
                print("PLAYER ERROR:", error)

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

    # ================= COMMANDS =================

    @app_commands.command(name="play", description="Tocar música do YouTube (nome ou link)")
    async def play(self, interaction: discord.Interaction, busca: str):
        await interaction.response.defer()

        if not interaction.user.voice:
            await interaction.followup.send("❌ Você precisa estar em um canal de voz.")
            return

        vc = interaction.guild.voice_client
        if not vc:
            vc = await interaction.user.voice.channel.connect()

        queues.setdefault(interaction.guild.id, [])

        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(busca, download=False)
            if "entries" in info:
                url = info["entries"][0]["url"]
                title = info["entries"][0]["title"]
            else:
                url = info["url"]
                title = info["title"]

        queues[interaction.guild.id].append(url)

        if not vc.is_playing():
            await self.play_next(interaction.guild)

        await interaction.followup.send(f"🎶 **Adicionado à fila:** {title}")

    @app_commands.command(name="skip", description="Pular a música atual")
    async def skip(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc and vc.is_playing():
            vc.stop()
            await interaction.response.send_message("⏭️ Música pulada")

    @app_commands.command(name="queue", description="Mostrar fila de músicas")
    async def queue(self, interaction: discord.Interaction):
        fila = queues.get(interaction.guild.id)

        if not fila:
            await interaction.response.send_message("📭 A fila está vazia.")
            return

        texto = ""
        for i, _ in enumerate(fila[:10], start=1):
            texto += f"{i}. Música\n"

        embed = discord.Embed(
            title="🎶 Fila de Reprodução",
            description=texto,
            color=discord.Color.blurple()
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="pause", description="Pausar música")
    async def pause(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc and vc.is_playing():
            vc.pause()
            await interaction.response.send_message("⏸️ Música pausada")

    @app_commands.command(name="resume", description="Retomar música")
    async def resume(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc and vc.is_paused():
            vc.resume()
            await interaction.response.send_message("▶️ Música retomada")

    @app_commands.command(name="leave", description="Remover o bot do canal")
    async def leave(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc:
            queues.pop(interaction.guild.id, None)
            await vc.disconnect()
            await interaction.response.send_message("👋 Saí do canal de voz")

    @app_commands.command(name="loop", description="Ativar/desativar loop")
    async def loop(self, interaction: discord.Interaction):
        config = get_config(interaction.guild.id)
        config["loop"] = not config["loop"]
        save_config(guild_config)
        await interaction.response.send_message(f"🔁 Loop: **{config['loop']}**")

    @app_commands.command(name="247", description="Manter o bot 24/7 no canal")
    async def stay(self, interaction: discord.Interaction):
        config = get_config(interaction.guild.id)
        config["stay"] = not config["stay"]
        save_config(guild_config)
        await interaction.response.send_message(f"🔒 24/7: **{config['stay']}**")

    @app_commands.command(name="volume", description="Alterar volume (0 a 100)")
    async def volume(self, interaction: discord.Interaction, valor: int):
        if not 0 <= valor <= 100:
            await interaction.response.send_message("❌ Volume entre 0 e 100.")
            return
        config = get_config(interaction.guild.id)
        config["volume"] = valor / 100
        save_config(guild_config)
        await interaction.response.send_message(f"🔊 Volume: **{valor}%**")

    @app_commands.command(name="help", description="Mostrar comandos do bot")
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎶 Comandos do Bot de Música",
            description="Controle completo de música",
            color=discord.Color.purple()
        )

        embed.add_field(name="/play", value="Tocar música (nome ou link)", inline=False)
        embed.add_field(name="/pause", value="Pausar música", inline=False)
        embed.add_field(name="/resume", value="Retomar música", inline=False)
        embed.add_field(name="/skip", value="Pular música", inline=False)
        embed.add_field(name="/queue", value="Ver fila", inline=False)
        embed.add_field(name="/loop", value="Loop da música", inline=False)
        embed.add_field(name="/volume", value="Alterar volume", inline=False)
        embed.add_field(name="/247", value="Bot 24/7", inline=False)
        embed.add_field(name="/leave", value="Remover bot", inline=False)

        embed.set_footer(text="Tocando uma rave, se quiser se juntar use /help 🎶")

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Music(bot))
