import logging
import traceback
from datetime import datetime
from string import Template

import boto3
import discord
import yaml
from boto3.dynamodb.conditions import Key
from discord import user
from discord.ext import commands

logging.basicConfig(filename='bot.log', level=logging.INFO,
                    format='%(asctime)s %(levelname)s - %(message)s')

sun_emoji = '\U00002600'
rain_emoji = '\U0001F327'
check_emoji = '\U00002705'
x_emoji = '\U0000274C'
lock_emoji = '\U0001F512'

dynamodb = boto3.resource("dynamodb", "us-east-2")


def get_message(guild_id):
    table = dynamodb.Table('bot')
    response = table.query(
        KeyConditionExpression=Key('id').eq(str(guild_id) + ".msg"))
    return response["Items"][0]["value"]


def get_config(guild_id):
    table = dynamodb.Table('bot')
    response = table.query(
        KeyConditionExpression=Key('id').eq(str(guild_id) + ".yaml"))
    return yaml.safe_load(response["Items"][0]["value"])


def get_token():
    table = dynamodb.Table('bot')
    response = table.query(
        KeyConditionExpression=Key('id').eq("token"))
    return response["Items"][0]["value"]


TOKEN = get_token()

intents = discord.Intents.default()
intents.members = True
intents.messages = True
intents.guilds = True

client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix="moo.", intents=intents,
                   activity=discord.Game(name="MoO | moo.help"))

properties = {}
message_templates = {}


def format_message(message, arg1, arg2, arg3):
    temp_obj = Template(message)
    return temp_obj.substitute(name=arg1, trial=arg2, no_show_ct=arg3)


@client.event
async def on_ready():
    logging.info("We have logged in as {0.user}".format(client))


@bot.command()
async def hello(ctx):
    await ctx.send("Hello!")


@client.event
async def on_message(message):
    if message.author == bot.user or message.content.startswith("moo."):
        return
    elif "bruh" in str.lower(message.content):
        logging.info("bruh")
        await message.add_reaction('\N{THUMBS UP SIGN}')


async def handle_confirmation_embed(reaction_payload, msg):
    e = msg.embeds[0]
    reactions = msg.reactions
    cleared = False
    filled = False
    for reaction in reactions:
        if reaction.emoji == sun_emoji and reaction.count == 2:
            filled = True
        if reaction.emoji == check_emoji and reaction.count == 2:
            cleared = True
    host = [x.value for x in e.fields if x.name == "Host"][0]
    event_channel = [x.value for x in e.fields if x.name == "Event Channel"][0]
    guild_id = [x.value for x in e.fields if x.name == "Guild ID"][0]
    logging.info("host", host, "cleared", cleared, "filled", filled,
          "event", event_channel, "guild id", guild_id)
    user = bot.get_user(reaction_payload.user_id)
    response_message = host + " hosted an event in " + event_channel + ". Filled: `" + \
        str(filled) + "`. Cleared: `" + str(cleared) + "`."
    guild = bot.get_guild(int(guild_id))
    channels = await guild.fetch_channels()
    guild_config = get_config(guild_id)["config"]
    run_log_channel_name = guild_config["run_log_channel"]["name"]
    run_log_channel = [
        x for x in channels if x.name == run_log_channel_name][0]
    await run_log_channel.send(response_message)


async def handle_reactions_to_bot_dm(reaction_payload, msg):
    if msg.embeds is not None and len(msg.embeds) == 1:
        e = msg.embeds[0]
        if e.title == "Confirmation" and reaction_payload.emoji.name == lock_emoji:
            await handle_confirmation_embed(reaction_payload, msg)


async def on_raw_reaction_add(reaction_payload):
    if reaction_payload.guild_id is None:
        channel = await bot.fetch_channel(reaction_payload.channel_id)
        msg = await channel.fetch_message(reaction_payload.message_id)
        if msg.author == bot.user and reaction_payload.user_id != bot.user.id:
            await handle_reactions_to_bot_dm(reaction_payload, msg)


def author_role(ctx, guild_config):
    if "role" in guild_config:
        role_name = guild_config["role"]
        role = discord.utils.find(
            lambda r: r.name == role_name, ctx.message.guild.roles)
    else:
        role = None
    return role


@bot.command(help="Report <user> as a no-show for <event>. <count> is the current number of no-shows for this member.")
async def noshow(ctx, user, event, count):
    try:
        guild_id = ctx.guild.id
        guild_config = get_config(guild_id)["config"]
        role = author_role(ctx, guild_config)
        if role is not None and role not in ctx.message.author.roles:
            logging.info("Not authorized: " + ctx.message.author.name)
            return
        id = ctx.message.mentions[0].id
        user = bot.get_user(id)
        message = get_message(guild_id)
        message = format_message(message, user, event, count)
        await user.send(message)
        channels = await ctx.guild.fetch_channels()
        channel_name = guild_config["channel"]["name"]
        channel = [x for x in channels if x.name == channel_name][0]
        await channel.send("noshow for <@" + str(id) + "> reported in channel `" + ctx.message.channel.name + "` at " +
                           datetime.today().strftime('%Y-%m-%d-%H:%M:%S') + ". `count: " + str(count) + "`")
    except Exception as e:
        logging.exception(e)
        user = bot.get_user(ctx.message.author.id)
        await user.send("I couldn't find a valid user for *" + user + "*. Make sure to mention (@) the user you're trying to noshow.")
    await ctx.message.delete()


@bot.command(help="Give your core a name and it will automatically create the role and the Apply and the Core Channels for you.")
async def createcore(ctx, corename):
    guild = ctx.guild
    guild_config = get_config(guild.id)["config"]
    role = author_role(ctx, guild_config)
    if role is not None and role not in ctx.message.author.roles:
        logging.info("Not authorized: " + ctx.message.author.name)
        return

    roles = guild.roles
    author = ctx.author
    logging.info(ctx.author.name)
    # Create new role.
    trialsrole = [x for x in roles if x.name ==
                  "--------------❖  CORES  ❖-------------"][0]
    # print(trialsrole.position)
    newrole = await guild.create_role(name="Core - " + corename)
    await author.add_roles(newrole)
    logging.info(newrole.name)
    positions = {
        newrole: trialsrole.position-1
    }
    await guild.edit_role_positions(positions=positions)
    # Create new channels for core.
    categories = guild.categories
    coregroups = [x for x in categories if str.lower(
        x.name) == "core groups"][0]
    opencores = [x for x in categories if str.lower(
        x.name) == "open core applications"][0]
    daedricprincerole = [x for x in roles if x.name == "Daedric Prince"][0]
    goldensaintsole = [x for x in roles if x.name == "Golden Saints"][0]
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        newrole: discord.PermissionOverwrite(read_messages=True),
        daedricprincerole: discord.PermissionOverwrite(read_messages=True),
        goldensaintsole: discord.PermissionOverwrite(read_messages=True)
    }
    await guild.create_text_channel(corename, overwrites=overwrites, category=coregroups)
    await guild.create_text_channel("Apply " + corename, overwrites=None, category=opencores)


@bot.command(help="Create a log entry for a trial led by <raid_lead> listed in <event_channel>")
async def archive(ctx, raid_lead, event_channel):
    try:
        guild_id = ctx.guild.id
        guild_config = get_config(guild_id)["config"]
        role = author_role(ctx, guild_config)
        if role is not None and role not in ctx.message.author.roles:
            logging.info("Not authorized: " + ctx.message.author.name)
            return
        id = ctx.message.author.id
        user = bot.get_user(id)
        info_msg = "React with :sunny: if the raid took place or :cloud_rain: if it was cancelled.\n\nReact with :white_check_mark: if the raid cleared or :x: if it did not.\n\nWhen you are done, react with :lock: to post the log entry."
        message = raid_lead + " hosted an event in channel " + event_channel + "."
        embedVar = discord.Embed(
            title="Confirmation", description="Please verify the following details to log this entry.", color=0x00ff00)
        embedVar.add_field(name="Host", value=raid_lead, inline=False)
        embedVar.add_field(
            name="Event Channel", value=ctx.message.channel_mentions[0].name, inline=False)
        embedVar.add_field(name="Guild Name", value=ctx.guild, inline=False)
        embedVar.add_field(name="Guild ID", value=ctx.guild.id, inline=False)
        embedVar.add_field(name="Instructions", value=info_msg, inline=False)
        sent_message = await user.send(embed=embedVar)
        await sent_message.add_reaction(sun_emoji)
        await sent_message.add_reaction(rain_emoji)
        await sent_message.add_reaction(check_emoji)
        await sent_message.add_reaction(x_emoji)
        await sent_message.add_reaction(lock_emoji)

    except Exception as e:
        logging.exception(e)
        user = bot.get_user(ctx.message.author.id)
        await user.send("I couldn't find a valid user for *" + user + "*. Make sure to mention (@) the user you're trying to noshow.")
    await ctx.message.delete()

bot.add_listener(on_message)
bot.add_listener(on_raw_reaction_add)
bot.run(TOKEN)
