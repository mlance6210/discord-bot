import discord
from discord import user
from discord.ext import commands
from datetime import datetime

TOKEN = open("token.txt", "r").readline()

intents = discord.Intents.default()
intents.members = True
intents.messages = True
intents.guilds = True

client = discord.Client(intents = intents)
bot = commands.Bot(command_prefix=".", intents = intents)

noshows = {}

@client.event
async def on_ready():
    print("We have logged in as {0.user}".format(client))

@bot.command()
async def hello(ctx):
    await ctx.send("Hello!")

@bot.command()
async def bruh(ctx):
    message = ctx.message
    if len(message.mentions) > 0:
            mentioned = message.mentions[0].id
            await message.delete()
            await message.channel.send("<@" + str(mentioned) +  "> sup bruh from <@" + str(message.author.id) + ">")


@client.event
async def on_message(message):
    if message.author == bot.user:
        return
    elif "bruh" in str.lower(message.content):
        await message.add_reaction('\N{THUMBS UP SIGN}')

@bot.command()
async def noshow(ctx, args):
    try :
        id = ctx.message.mentions[0].id
        user = bot.get_user(id)
        await user.send("This is currently a test message. If you're receiving a lot of messages from me, someone might be trolling you. " + \
            "You have been reported as a _no show_ for a scheduled event in channel " + ctx.message.channel.mention + ". Something about the guild rules " + \
                "re: noshows should go here.")
        channels = await ctx.guild.fetch_channels()
        channel = [x for x in channels if x.name == "bot-posts-test"][0]
        await channel.send("noshow for <@" + str(id) +"> in " + ctx.message.channel.mention + " reported at " + datetime.today().strftime('%Y-%m-%d-%H:%M:%S'))
    except Exception:
        user = bot.get_user(ctx.message.author.id)
        await user.send("I couldn't find a valid user for *" + args + "*. Make sure to mention (@) the user you're trying to noshow.")
    await ctx.message.delete()
    


bot.add_listener(on_message)
bot.run(TOKEN)