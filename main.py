import discord
from discord import user
from discord.ext import commands
from datetime import datetime
from string import Template
import traceback

TOKEN = open("token.txt", "r").readline()

intents = discord.Intents.default()
intents.members = True
intents.messages = True
intents.guilds = True

client = discord.Client(intents = intents)
bot = commands.Bot(command_prefix="moo.", intents = intents, activity=discord.Game(name="MoO | moo.help"))

properties = {}
message_templates = {}


def get_message(guild_id):
    if guild_id in message_templates:
        return message_templates[guild_id]
    message = ""
    with open("messages/" + str(guild_id) + ".msg", "r") as f:
        message = f.readlines()
    message = "".join(message)
    message_templates[guild_id] = message
    return message

def get_config(guild_id):
    if guild_id in properties:
        return properties[guild_id]
    import yaml
    config = None
    with open("messages/" + str(guild_id) + ".yaml", "r") as f:
        config = yaml.safe_load(f)
    properties[guild_id] = config
    return config

def format_message(message, arg1, arg2, arg3):
    temp_obj = Template(message)
    return temp_obj.substitute(name=arg1, trial=arg2, no_show_ct=arg3)


@client.event
async def on_ready():
    print("We have logged in as {0.user}".format(client))

@bot.command()
async def hello(ctx):
    await ctx.send("Hello!")

@client.event
async def on_message(message):
    if message.author == bot.user or message.content.startswith("moo."):
        return
    elif "bruh" in str.lower(message.content):
        await message.add_reaction('\N{THUMBS UP SIGN}')

@bot.command(help="Report <user> as a no-show for <event>. <count> is the current number of no-shows for this member.")
async def noshow(ctx, user, event, count):
    try :
        guild_id = ctx.guild.id
        guild_config = get_config(guild_id)["config"]
        if "role" in guild_config:
            role_name = guild_config["role"]
            role = discord.utils.find(lambda r: r.name == role_name, ctx.message.guild.roles)
        else:
            role = None
        if role is not None and role not in ctx.message.author.roles:
            print("Not authorized")
            return
        id = ctx.message.mentions[0].id
        user = bot.get_user(id)
        message = get_message(guild_id)
        message = format_message(message, user, event, count)
        await user.send(message)
        channels = await ctx.guild.fetch_channels()
        channel_name = guild_config["channel"]["name"]
        channel = [x for x in channels if x.name == channel_name][0]
        await channel.send("noshow for <@" + str(id) +"> reported in channel `" + ctx.message.channel.name + "` at " + \
            datetime.today().strftime('%Y-%m-%d-%H:%M:%S') +". `count: " + str(count) + "`")
    except Exception as e:
        traceback.print_exc(e)
        user = bot.get_user(ctx.message.author.id)
        await user.send("I couldn't find a valid user for *" + user + "*. Make sure to mention (@) the user you're trying to noshow.")
    await ctx.message.delete()
    


bot.add_listener(on_message)
bot.run(TOKEN)


