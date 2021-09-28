import asyncio
import atexit
import datetime
import logging
import os
import random
import re
import sqlite3
import pytz

import discord
from discord.ext import commands
from discord.ext.commands import CommandNotFound
from discord.ext.commands import has_permissions

#estabelece a conexão p/ meu banco de dados "principal" (eu realmente tenho que re-escrever isso)
conn = sqlite3.connect('deletes.db')
c = conn.cursor()

#ativa os intents personalizados (isso não vai funcionar em bots com mais de 100 guilds)
intents = discord.Intents.all()
intents.members = True
intents.presences = True

PREFIX="="
PRESENCE = open('presence.txt','r').read() #arquivo aonde eu salvo o presence do bot (isso devia ser feito usando uma
#chamada para db, mas tenho que re-escrever isso dps
bot = commands.Bot(command_prefix=PREFIX, help_command=None, case_insensitive=True, 
intents=intents, activity=discord.Activity(type=discord.ActivityType.watching, name=f'{PRESENCE}')) #define o que é o bot
TOKEN = os.getenv("HOTTIES_TOKEN") #pega o token (eu deveria usar um virtual env aqui, tenho q re-escrever dps)
logging.basicConfig(level=logging.INFO)
fuso = pytz.timezone('America/Sao_Paulo') #define o fuso (isso é muito importante pra dps)


#
# Módulo de logging
#
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO) #smp deixe em INFO a não ser que você precise de ver algo q está dando errado
handler = logging.FileHandler(filename=f'hottiesbot.log', encoding='utf-8', mode='w')
#o W no mode='w' é para ele iniciar um novo arquivo toda vez que eu re-iniciar o bot
#isso foi feito por que eu reiniciava muito ele no começo, e isso gerava um puta spam de arquivos
#caso você queira ter um log "permanente", coloque mode='a'
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

#
# Logging - filtro
#
fbot = logging.getLogger('filterbot')
if fbot.hasHandlers(): #eu verifico aqui se o log de filtros já existe, e se existir, limpo e dps defino tudo dnv
    #isso é bom caso você reinicie seu bot mtas vezes tmb (no meu caso, eu reiniciava)
    print(len(fbot.handlers))
    fbot.handlers.clear()
handler2 = logging.FileHandler(filename=f'filterbot.log', encoding='utf-8', mode='a')
handler2.setFormatter(logging.Formatter('%(asctime)s:%(name)s: %(message)s'))
fbot.addHandler(handler2)

#
# Logging - moderação
#
modlogs = logging.getLogger('modlogs')
if modlogs.hasHandlers():
    print(len(modlogs.handlers))
    modlogs.handlers.clear()
handler4 = logging.FileHandler(filename=f'moderation.log', encoding='utf-8', mode='a')
handler4.setFormatter(logging.Formatter('%(asctime)s:%(name)s: %(message)s'))
modlogs.addHandler(handler4)

#
# Logging - mensagens deletadas
#
deletelog = logging.getLogger('deleted-message')
if deletelog.hasHandlers():
    print(len(deletelog.handlers))
    deletelog.handlers.clear()
handler3 = logging.FileHandler(filename=f'deletes.log', encoding='utf-8', mode='a')
handler3.setFormatter(logging.Formatter('%(name)s: %(message)s'))
deletelog.addHandler(handler3)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}({bot.user.id}) running {discord.__version__}") #esse código é executado toda vez que você inicia seu bot
    #as vezes ele pode ser executado quando há reconexão do bot, então não coloque algo aqui que você não possa executar várias vezes


#O check abaixo serve para bloquear comandos pela DM do seu bot, de maneira global
#Eu deixo isso desativado pq alguns comandos usam a dm do bot
#Isso afeta todas as cogs do bot
# @bot.check
# async def globally_block_dms(ctx):
#     return ctx.guild is not None

#Mensagem global de "comando não encontrado"
#Afeta todos os comandos, em todas as cogs
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound) and ctx.message.channel is not ctx.author.dm_channel:
        embednotfound = discord.Embed(description=f'<:IconError:862541043702693950> Comando não encontrado', color=0xff0000)
        await ctx.reply(embed=embednotfound, delete_after=10)
        await asyncio.sleep(10)
        await ctx.message.delete()
        #ele deleta ambas as mensagens depois de 10 segundos
    elif isinstance(error, commands.MissingPermissions):
        emessage = f"Você não tem permissão para utilizar esse comando"
        embederror=discord.Embed(title="<:IconError:862541043702693950> Um erro aconteceu!", description=emessage, color=0xff0000, timestamp=datetime.datetime.utcnow())
        embederror.set_footer(text=f'Motivo do erro: commands.MissingPermissions | Se acha que isso é um erro contate o suporte | ')
        await ctx.reply(embed=embederror, delete_after=15)
        await asyncio.sleep(15)
        try: #Preciso desse loop de try // except por que você deletar uma mensagem pode gerar um erro de você não ter permissão
            await ctx.message.delete()
        except discord.errors.Forbidden: #caso você esteja na dm ou caso o bot não tenha perm de adm, isso pode acontecer, caso aconteça, ele só passa e não deleta a mensagem do usuário
            pass

#
# Comando - recarregar
#
# Esse comando recarrega um módulo do bot
@bot.command(name='reload', hidden=True)
@has_permissions(administrator=True)
async def reload(ctx, *, module : str=None):
    if module is None: #se você não dá um argumento
        await ctx.reply("<:question:864592258204172328> Uso do comando:\n`=reload cogs.módulo` (trocar módulo pelo nome do módulo)")
        return
    else:
        try: #ele vai tentar recarregar esse módulo
            msg = await ctx.reply("<a:loading:869766046733713549> Recarregando cog")
            bot.reload_extension(f'{module}')
            await msg.edit(content=":white_check_mark: | Cog recarregada")
        except Exception as e: #se não conseguir:
            await msg.edit(content='<:IconError:862541043702693950> | Impossível recarregar cog. \nMensagem de erro: `{}: {}`'.format(type(e).__name__, e))

#
# Módulo - mensagens deletadas
#
#Função para pegar números aleatórios (e únicos, de acordo com a DB)
async def randomnumber():
    while True: #inicia o loop
        mid = random.randint(1000, 9999)
        c.execute("SELECT id FROM global WHERE id = ?", (mid,))
        exists = c.fetchone()
        if exists is None:
            logger.info(f'Got random number {mid}')
            return mid #fecha o loop e retorna o valor
        else:
            logger.info('trying to get random number again, random already exists')
            pass #retorna ao início do loop

allowed = [862506804180680744,862515353661472769,862515398272745480,862511804722184242,862515487196053514,862527320379490304]
blacklist = ['mp4','webm','avi', 'mov', '3gp', 'mkv', 'm4u', 'mpg', 'mpeg']
@bot.event #evento aonde ele captura as mensagens deletadas
async def on_message_delete(message):
    if not message.author.bot:
        date = datetime.datetime.now()
        datesp = date.astimezone(fuso)
        #
        # Verificação para não capturar certos comandos
        # você pode fazer uma verificação decente só implementando o if message.content.startswith(PREFIX)
        # assim ele vai ignorar de salvar qualquer comando do bot, porém, eu não quis fazer assim
        # mas você pode
        if message.content.startswith("=desabafar"):
            return
        if message.content.startswith("=desabafo"):
            return
        if message.content.startswith(";eununca"):
            return
        if message.content.startswith("=sugestao"):
            return
        if message.content.startswith("=sugerir"):
            return
        if message.attachments:
            try:
                for attachment in message.attachments:
                    if message.channel.id in allowed and attachment.filename.split('.')[-1] in blacklist: #verifica se é um vídeo e se foi mandado nos canais permitidos
                        mid = await randomnumber()
                        filename = str(attachment.filename)
                        c.execute("INSERT INTO global (id, filename) VALUES (?,?)",
                                  (mid, filename))
                        deletelog.info(f'Vídeo deletado - [{message.author.name}] [{message.channel.name}] [' + datesp.strftime(
                            '%d/%m-%H:%M') + f']: Arquivo - =rfile {mid}')
                        await attachment.save(fp="deletes/{}".format(attachment.filename)) #isso salva na sua máquina o arquivo enviado
                        conn.commit()
                    if attachment.filename.split('.')[-1] not in blacklist: #verifica se não é um vídeo (e não está nos canais permitidos)
                        # (eu adicionei isso por que ele já salva os vídeos que o bot de filtro pega e só alguns cargos podem mandar vídeo sem restrição nos chats gerais
                        mid = await randomnumber()
                        filename = str(attachment.filename)
                        c.execute("INSERT INTO global (id, filename) VALUES (?,?)",
                                  (mid, filename))
                        deletelog.info(f'Arquivo deletado - [{message.author.name}] [{message.channel.name}] [' + datesp.strftime(
                            '%d/%m-%H:%M') + f']: Arquivo - =rimg {mid}')
                        await attachment.save(fp="deletes/{}".format(attachment.filename))
                        conn.commit() #a cada modificação que você fizer no banco de dados, SEMPRE lembre-se de usar conn.commit() para salvar suas modificações
                    break
            except Exception as e:
                logger.error('Unknown error\nError: {}'.format(e)) #caso dê algum erro
        if not message.attachments: #se não contem um vídeo
            deletelog.info(f'Mensagem deletada - [{message.author.name}] [{message.channel.name}] [' + datesp.strftime('%d/%m-%H:%M')+ f'] : {message.content}')


#
# Filtro de vídeos/links
#
# Abaixo tem os IDS do cargo de beta e mizunoto
# Também tem uma expressão para pegar os links enviados
blacklistedroles = [862534872078090253,862603092989575170]
link = re.compile(r'https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,4}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)')
@bot.event
async def on_message(message):
    if link.search(message.content) is not None:
        member = await discord.Guild.query_members(self=bot.get_guild(862471633805377587), user_ids=[message.author.id]) #pega o objeto de member do autor da mensagem
        member = member[0]
        rids = list(map(str, [r.id for r in member.roles]))
        roleids = list(map(int,rids))
        if any(p in roleids for p in blacklistedroles):
            if not message.author.guild_permissions.administrator: #verifica se é um adm beta/mizunoto
                fbot.warning(f'[FILTRO-LINK] {message.author.name}[{message.author.id}] postou "{message.clean_content}" em {message.channel.name}[{message.channel.id}]')
                await message.delete()
                await message.channel.send(f'<:IconError:862541043702693950> | {message.author.mention} Você não pode mandar links aqui.\nSomente o rank Mizunoe (ou acima) pode enviar links no servidor.',delete_after=5)
    #Filtro de vídeos
    try:
        for attachment in message.attachments:
            media = bot.get_channel(862506804180680744) #pega o id do canal de mídia
            if message.channel.id not in allowed and attachment.filename.split('.')[-1] in blacklist:
                date = datetime.datetime.now()
                datesp = date.astimezone(fuso) #lembra que eu falei q era importante o fuso? eh bom vc ter salvo aí ó
                if message.author.guild_permissions.administrator or message.author.bot == True: #se for adm ou bot:
                    fbot.info(f"[{attachment.filename}] Media sent by admin/bot[{message.author}] in {message.channel} at " + datesp.strftime('%d/%m/%Y - %H:%M:%S'))
                    break #quebra o loop
                logmsg = (f"[{attachment.filename}] Deleting message in {message.channel} sent by {message.author} at " + datesp.strftime('%d/%m/%Y - %H:%M:%S'))
                fbot.info(logmsg)
                medianotallowed = discord.Embed(description=f'<:IconError:862541043702693950> Ei {message.author.mention}, evite de postar vídeos no {message.channel.mention}!\nVocê pode postá-los no {media.mention}', color=0xff0000)
                medianotallowed.set_image(url="https://i.ibb.co/h1MPMCQ/image.png")
                await message.reply(embed=medianotallowed,delete_after=13)
                await attachment.save(fp="videos/{}".format(attachment.filename))
                await message.delete()
            break
        await bot.process_commands(message)
    except:
        logger.error('Unknown error')
        await bot.process_commands(message)
#
#Fim do filtro
#



#
# Função que carrega cogs
#
# As cogs são uma maneira melhor de organizar o seu bot
# Nesse bot eu tenho: utility, voice, report, fun
def cogs():
    for file in os.listdir("cogs"): #ele vai carregar todos os arquivos terminados em .py na pasta cogs
        if file.endswith(".py"):
            try:
                bot.load_extension(f'cogs.{file[:-3]}') #carrega a cog
            except Exception as e: #se não:
                exc = '{}: {}'.format(type(e).__name__, e)
                logger.error('Failed to load extension {}\n{}'.format(file, exc))

def exit_handler(): #aqui eu fecho a conexão do banco de dados "principal"
    logger.info("Closing requested, closing now")
    conn.close()
    logger.info("Closed the connection")

#
# Esse código no final do script é necessário pra carregar o bot
# Sem ele, o bot não inicia e conecta ao discord
#
if __name__ == "__main__":
    cogs() #carrega as cogs
    bot.run(TOKEN, reconnect=True) #inicia o bot
    atexit.register(exit_handler) #registra o código que executa quando eu fecho o bot