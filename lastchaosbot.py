import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
from pytz import timezone
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = os.getenv('DISCORD_GUILD_ID')

intents = discord.Intents.default()
intents.message_content = True
intents.message_mentions = True

bot = commands.Bot(command_prefix='/', intents=intents)

boss_respawn_times = {
    'balrog': timedelta(minutes=50),
    'astarte': timedelta(hours=1),
    'flamejante': timedelta(hours=1, minutes=7),
    'solaris': timedelta(hours=1, minutes=40),
    'dagon_day': timedelta(minutes=20),
    'dagon_night': timedelta(minutes=40)
}

respawn_channel_id = 1203440546111299764  # Substitua pelo ID do canal "drop-boss"

@tasks.loop(minutes=1)
async def check_respawn_times():
    for server in boss_timers:
        for boss in boss_timers[server]:
            respawn_time = boss_timers[server][boss]['respawn_time']
            time_until_respawn = respawn_time - datetime.now(timezone('America/Sao_Paulo'))

            if 0 < time_until_respawn.total_seconds() < 180 and not boss_timers[server][boss]['notified']:
                channel = bot.get_channel(respawn_channel_id)
                await channel.send(f"Faltam 3 minutos para o {boss} nascer no servidor {server} às {respawn_time.strftime('%H:%M')}.")
                boss_timers[server][boss]['notified'] = True

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    check_respawn_times.start()

boss_timers = {}

@bot.command(name='horario')
async def show_respawn_times(ctx):
    server = str(ctx.guild.id)

    if server not in boss_timers or not boss_timers[server]:
        await ctx.send("Nenhum boss foi registrado neste servidor.")
        return

    response = f"**{ctx.guild.name}**\n\n"

    for boss in boss_timers[server]:
        respawn_time = boss_timers[server][boss]['respawn_time']
        response += f"Respawn {boss.capitalize()} às {respawn_time.strftime('%H:%M')}\n"

    await ctx.send(response)

@bot.command(name='balrog', aliases=['astarte', 'flamejante', 'solaris', 'dagon'])
async def register_boss(ctx, *args):
    boss_name = ctx.command.name
    server = str(ctx.guild.id)

    if boss_name == 'dagon' and args:
        death_time = datetime.strptime(args[0], '%H:%M')
        if 1 <= death_time.hour <= 18:
            respawn_time = death_time + boss_respawn_times['dagon_day']
        else:
            respawn_time = death_time + boss_respawn_times['dagon_night']
    elif args:
        death_time = datetime.strptime(args[1], '%H:%M')
        respawn_time = death_time + boss_respawn_times[boss_name]
    else:
        await ctx.send("Formato inválido. Use: /<nome_do_boss> <servidor> <horário_da_morte>")
        return

    if server not in boss_timers:
        boss_timers[server] = {}

    boss_timers[server][boss_name] = {'respawn_time': respawn_time, 'notified': False}
    await ctx.send(f"Boss {boss_name.capitalize()} registrado para o servidor {ctx.guild.name} às {respawn_time.strftime('%H:%M')}.")

bot.run(TOKEN)
