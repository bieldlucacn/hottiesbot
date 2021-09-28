import asyncio
import os
import discord
from discord.ext import commands
from discord.ext.commands import CommandNotFound

intents = discord.Intents.all()
intents.members = True
intents.presences = True

PREFIX="="
bot = commands.Bot(command_prefix=PREFIX, help_command=None, case_insensitive=True, intents=intents)
TOKEN = os.getenv("HOTTIES_TOKEN")

#
#
#   Arquivo de manutenção
#   O que eu faço aqui?
#
#   Sempre que eu preciso de modificar um código no bot ou em algum banco de dados que manter ele rodando
#   poderia quebrar esse banco de dados, eu coloco ele em manutenção
#   Basicamente, esse arquivo é um script que ignora todos os comandos e funcionalidades do bot e não carrega nenhuma cog
#   Ou seja, sempre que você tenta usar um comando, ele só retorna o erro de comando não encontrado
#   A mensagem respondendo o comando não encontrado é a mensagem avisando que está em manutenção
#
#

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}({bot.user.id}) running {discord.__version__} // MAINTENANCE MODE")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f'😥 em manutenção'))


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound) and ctx.message.channel is not ctx.author.dm_channel:
        embednotfound = discord.Embed(description=f':warning: oii eu estou em manutenção\nvolto em breve\n**motivo:** `motivo vai aqui`', color=0xff0000)
        await ctx.reply(embed=embednotfound, delete_after=10)
        await asyncio.sleep(10)
        await ctx.message.delete()

if __name__ == "__main__":
    bot.run(TOKEN, reconnect=True)