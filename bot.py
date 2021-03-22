import discord
import sqlite3
import os
import helpers.embed_helper
import helpers.role_helper
import helpers.channel_helper
import cogs.colors
import cogs.minecraft
import math
import asyncio
import datetime

from configparser import ConfigParser
from discord.ext import commands
from importlib import import_module

# CONFIG INFO #
cfg = ConfigParser()
cfg.read('config.ini')

# BOT INFO #
bot_token = cfg.get('Bot', 'token')
bot_prefix = cfg.get('Bot', 'command_prefix')
bot_message = cfg.get('Bot', 'status_message')
bot_author_id = 106882411781947392
intents = discord.Intents.all()
client = commands.Bot(command_prefix=bot_prefix, intents=intents)

client.remove_command('help')

# DB INFO #
connection = sqlite3.connect("./db/config.db")
db = connection.cursor()

# EVENTS #

# READY EVENT #
@client.event
async def on_ready():
    db.execute('CREATE TABLE IF NOT EXISTS roles(role_name text unique, role_id integer)')
    db.execute('CREATE TABLE IF NOT EXISTS channels(channel_name text unique, channel_id integer)')
    connection.commit()
    await client.change_presence(
        activity=discord.Game(name=f'{bot_message} | {bot_prefix}help')
    )

    for member in client.guilds[0].members:
        if not member.pending and not member.bot:
            if await helpers.role_helper.is_role_defined('user'):
                if not await helpers.role_helper.has_role(client.guilds[0], member.id, 'user'):
                    await client.guilds[0].get_member(member.id).add_roles(
                        client.guilds[0].get_role(
                            await helpers.role_helper.get_role_id('user')
                        )
                    )

    print(f'Bot ({client.user}) is now online')

# JOIN EVENT #
@client.event
async def on_member_join(member):
    await asyncio.sleep(1)
    message = f'{member} has joined the server.' if not member.pending else f'{member} has joined the server. Awaiting Screening.'

    print(message)

# LEAVE EVENT #
@client.event
async def on_member_remove(member):
    await asyncio.sleep(1)

    if await cogs.colors.has_color_role(member.id):
        await cogs.colors.delete_color_role(client.guilds[0], member.id)

    if await cogs.minecraft.has_whitelist(member.id):
        await cogs.minecraft.whitelist_remove_user(member.id)

    leave_message = f'{member} has left the server.' if not member.pending else f'{member} has left the server. (Member was still pending.)'

    if await helpers.channel_helper.is_channel_defined('admin') and client.guilds[0].id == 462530786667659265:
        await client.guilds[0].get_channel(
            await helpers.channel_helper.get_channel_id('admin')
        ).send(leave_message)

    if await helpers.channel_helper.is_channel_defined('joins'):
        channel = member.guild.get_channel(await helpers.channel_helper.get_channel_id('joins'))

        async for message in channel.history(limit=20):
            if message.author.id == member.id:
                await channel.delete_messages([message])

    print(leave_message)

# UPDATE EVENT #
@client.event
async def on_member_update(before, after):

    before_roles = before.roles
    before_roles.reverse()
    after_roles = after.roles
    after_roles.reverse()

    # GAIN ROLE #
    if len(before_roles) < len(after_roles):
        new_role = next(role for role in after_roles if role not in before_roles)
        print(f'{before}({before.id}) has gained role: {new_role}({new_role.id})')

    # LOSE ROLE #
    if len(before.roles) > len(after.roles):
        lost_role = next(role for role in before_roles if role not in after_roles)
        print(f'{before}({before.id}) has lost role: {lost_role}({lost_role.id})')

        if await helpers.role_helper.is_role_defined('booster'):
            if lost_role == client.guilds[0].get_role(int(await helpers.role_helper.get_role_id('booster'))):
                if await cogs.colors.has_color_role(before.id):
                    await cogs.colors.delete_color_role(client.guilds[0], before.id)

        if await helpers.role_helper.is_role_defined('sub'):
            if lost_role == client.guilds[0].get_role(int(await helpers.role_helper.get_role_id('sub'))):
                if await cogs.minecraft.has_whitelist(before.id):
                    await cogs.minecraft.whitelist_remove_user(before.id)

    if await helpers.role_helper.is_role_defined('user'):
        if after.pending is False and not await helpers.role_helper.has_role(client.guilds[0], before.id, 'user'):
            print(f'{after}({after.id}) has agreed to the rules.')
            await client.guilds[0].get_member(after.id).add_roles(
                client.guilds[0].get_role(
                    await helpers.role_helper.get_role_id('user')
                )
            )

@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.NoPrivateMessage):
        await ctx.send(
            embed=await helpers.embed_helper.create_error_embed('You cannot run commands in Private Messages.')
        )
        return
    if isinstance(error, commands.CheckFailure):
        await ctx.send(
            embed=await helpers.embed_helper.create_error_embed('You do not have permission to use this command.')
        )
        return
    raise error

@client.event
async def on_member_ban(guild, user):
    ban_list = await guild.bans()
    if await helpers.channel_helper.is_channel_defined('mod'):
        channel = client.guilds[0].get_channel(await helpers.channel_helper.get_channel_id('mod'))
        ban_giver = ''

        await asyncio.sleep(2)

        async for log in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban, after=(datetime.datetime.now() - datetime.timedelta(seconds=5))):
            ban_giver = log.user

        embed = discord.Embed(
            title='User Banned!',
            color=await get_bot_color(),
            description=f'{ban_giver.mention} banned {user}.'
        )
        embed.set_author(name=str(user), icon_url=user.avatar_url)

        for ban in ban_list:
            if ban.user.id == user.id:
                if ban.reason is not None:
                    embed.add_field(name='Reason', value=ban.reason, inline=False)

        embed.set_footer(text=f'Discord ID: {user.id}')
        if not ban_giver.bot:
            await channel.send(embed=embed)

# COMMANDS #

# BOT COMMAND #
@client.command()
@commands.guild_only()
async def bot(ctx):
    bot_author = client.get_user(bot_author_id)
    embed = discord.Embed(
        title=client.user.name,
        description=f'This bot was made by {bot_author.mention} in Python using the discord.py API.',
        color=await get_bot_color()
    )
    embed.set_author(name=bot_author, icon_url=bot_author.avatar_url)
    embed.add_field(
        name='Twitch',
        value='https://www.twitch.tv/spiderpigethan',
        inline=False
    )

    embed.add_field(
        name='Twitter',
        value='https://twitter.com/SpiderPigEthan',
        inline=False
    )

    await ctx.send(embed=embed)
    print(f'{ctx.author}({ctx.author.id}) executed Bot command.')

# SETROLE COMMAND #
@client.command()
@commands.has_permissions(administrator=True)
@commands.guild_only()
async def setrole(ctx, role_name, *, text):

    print(f'{ctx.author}({ctx.author.id}) executed SetRole command.')

    valid_roles = ['sub', 'booster', 'mod', 'user', 'movie', 'game']
    mentioned_roles = ctx.message.role_mentions
    role_name = role_name.lower()
    if len(mentioned_roles) > 0:
        role = mentioned_roles[0]
        role_is_valid = False
        for rname in valid_roles:
            if rname == role_name:
                role_is_valid = True
                pass
        if role_is_valid:
            if await helpers.role_helper.is_role_defined(role_name):
                db.execute('UPDATE roles SET role_id=? WHERE role_name=?', (role.id, role_name))
            else:
                db.execute('INSERT INTO roles VALUES (?,?)', (role_name, role.id))
            print(f'{role_name} role set to {role}({role.id})')
            await ctx.send(
                embed=await helpers.embed_helper.create_success_embed(
                    f'`{role_name}` role set to {role.mention}',
                    await get_bot_color()
                )
            )
            connection.commit()
        else:
            await ctx.send(
                embed=await helpers.embed_helper.create_error_embed(
                    f'`{role_name}` is not a valid role name.'
                )
            )
    else:
        await ctx.send(
            embed=await helpers.embed_helper.create_error_embed(
                'Please mention the role you would like to use.'
            )
        )

# SETCHANNEL COMMAND #
@client.command()
@commands.has_permissions(administrator=True)
@commands.guild_only()
async def setchannel(ctx, channel_name, *, text):

    print(f'{ctx.author}({ctx.author.id}) executed SetChannel command.')

    valid_roles = ['bot', 'booster', 'mod', 'admin', 'general', 'joins']
    mentioned_channels = ctx.message.channel_mentions
    channel_name = channel_name.lower()
    if len(mentioned_channels) > 0:
        channel = mentioned_channels[0]
        channel_is_valid = False
        for cname in valid_roles:
            if cname == channel_name:
                channel_is_valid = True
                pass
        if channel_is_valid:
            if await helpers.channel_helper.is_channel_defined(channel_name):
                db.execute('UPDATE channels SET channel_id=? WHERE channel_name=?', (channel.id, channel_name))
            else:
                db.execute('INSERT INTO channels VALUES (?,?)', (channel_name, channel.id))
            print(f'{channel_name} channel set to {channel}({channel.id})')
            await ctx.send(
                embed=await helpers.embed_helper.create_success_embed(
                    f'`{channel_name}` channel set to {channel.mention}',
                    await get_bot_color()
                )
            )
            connection.commit()
        else:
            await ctx.send(
                embed=await helpers.embed_helper.create_error_embed(
                    f'`{channel_name}` is not a valid channel name.'
                )
            )
    else:
        await ctx.send(
            embed=await helpers.embed_helper.create_error_embed(
                'Please mention the channel you would like to use.'
            )
        )

# LOAD COMMAND #
@client.command()
@commands.has_permissions(administrator=True)
@commands.guild_only()
async def enable(ctx, extension):
    client.load_extension(f'cogs.{extension}')
    await enable_cog(extension)
    print(f'{ctx.author}({ctx.author.id}) executed Enable command on module {extension}.')
    await ctx.send(
        embed=await helpers.embed_helper.create_success_embed(
            f'Module `{extension}` has been enabled.',
            await get_bot_color()
        )
    )

# UNLOAD COMMAND #
@client.command()
@commands.has_permissions(administrator=True)
async def disable(ctx, extension):
    client.unload_extension(f'cogs.{extension}')
    await disable_cog(extension)
    print(f'{ctx.author}({ctx.author.id}) executed Disable command on module {extension}.')
    await ctx.send(
        embed=await helpers.embed_helper.create_success_embed(
            f'Module `{extension}` has been disabled.',
            await get_bot_color()
        )
    )

# RELOAD COMMAND #
@client.command()
@commands.has_permissions(administrator=True)
@commands.guild_only()
async def reload(ctx, extension):
    client.unload_extension(f'cogs.{extension}')
    client.load_extension(f'cogs.{extension}')
    print(f'{ctx.author}({ctx.author.id}) executed Reload command on module {extension}.')
    await ctx.send(
        embed=await helpers.embed_helper.create_success_embed(
            f'Module `{extension}` has been reloaded.',
            await get_bot_color()
        )
    )

@client.command()
@commands.guild_only()
async def modules(ctx, page=1):

    print(f'{ctx.author}({ctx.author.id}) executed Modules command.')

    module_list = await get_cogs()

    modules_per_page = 6

    total_pages = math.ceil(len(module_list) / modules_per_page)

    if page > total_pages:
        await ctx.send(
            embed=await helpers.embed_helper.create_error_embed(
                f'That page does not exist, the last page is {total_pages}.'
            )
        )
    elif page < 1:
        await ctx.send(
            embed=await helpers.embed_helper.create_error_embed(
                'That page does not exist, the first page is 1.'
            )
        )
    else:
        embed = discord.Embed(
            title='Modules',
            color=await get_bot_color()
        )
        number = min((modules_per_page * page), len(module_list))

        for i in range((modules_per_page * (page - 1)), number):
            module_status = 'Enabled' if bool(int(module_list[i][1])) else 'Disabled'
            if i == modules_per_page * (page - 1):
                embed.add_field(name='Module', value=module_list[i][0], inline=True)
                embed.add_field(name='Description', value=module_list[i][2], inline=True)
                embed.add_field(name='Status', value=module_status, inline=True)
            else:
                embed.add_field(name='\u200b', value=module_list[i][0], inline=True)
                embed.add_field(name='\u200b', value=module_list[i][2], inline=True)
                embed.add_field(name='\u200b', value=module_status, inline=True)
        embed.add_field(name='\u200b', value=f'Page [{page}/{total_pages}]', inline=True)
        await ctx.send(
            embed=embed
        )

@client.command()
@commands.has_permissions(administrator=True)
@commands.guild_only()
async def status(ctx, *, message):
    print(f'{ctx.author}({ctx.author.id}) executed Status command.')
    global bot_message
    bot_message = message
    cfg_file = open('config.ini', 'w')
    cfg.set('Bot', 'status_message', message)
    cfg.write(cfg_file)
    cfg_file.close()
    await client.change_presence(
        activity=discord.Game(name=f'{bot_message} | {bot_prefix}help')
    )

@client.command()
@commands.guild_only()
async def whois(ctx, mention_user=None):
    print(f'{ctx.author}({ctx.author.id}) executed WhoIs command.')
    if len(ctx.message.mentions) == 0 and mention_user is None:
        user = ctx.author
    else:
        user = ctx.message.mentions[0]

    embed = discord.Embed(
        description=user.mention,
        color=user.color
    )
    embed.set_author(name=user, icon_url=user.avatar_url)
    created_at = user.created_at
    joined_at = user.joined_at

    embed.add_field(
        name='Registered',
        value=created_at.strftime('%a, %b %d, %Y %I:%M %p'),
        inline=True
    )
    await helpers.embed_helper.add_blank_field(embed, True)

    embed.add_field(
        name='Joined',
        value=joined_at.strftime('%a, %b %d, %Y %I:%M %p'),
        inline=True
    )
    role_message = ''
    role_list = user.roles
    role_list.reverse()

    for role in role_list:
        if role.name != '@everyone':
            role_message += f'{role.mention} '

    embed.add_field(
        name=f'Roles [{len(user.roles)-1}]',
        value=role_message,
        inline=False
    )

    perm_message = ''

    for perm in user.guild_permissions:
        if await helpers.role_helper.is_role_defined('user'):
            if perm not in ctx.guild.get_role(
                    await helpers.role_helper.get_role_id('user')
            ).permissions:
                if perm[1]:
                    perm_message += f'{perm[0]}, '

    if len(perm_message) > 0:
        embed.add_field(
            name='Special Permissions',
            value=perm_message,
            inline=False
        )

    embed.set_thumbnail(url=user.avatar_url)
    embed.set_footer(text=f'ID: {user.id}')

    await ctx.send(
        embed=embed
    )

@client.command()
@commands.check(helpers.role_helper.is_mod)
@commands.guild_only()
async def lookup(ctx, user_id):
    print(f'{ctx.author}({ctx.author.id}) executed Lookup command.')
    try:
        user = await client.fetch_user(user_id)
        embed = discord.Embed(
            color=await get_bot_color(),
            description=user.mention
        )
        embed.set_author(name=str(user), icon_url=user.avatar_url)
        embed.set_thumbnail(url=user.avatar_url)
        created_at = user.created_at

        embed.add_field(
            name='Registered',
            value=created_at.strftime('%a, %b %d, %Y %I:%M %p'),
            inline=True
        )

        await ctx.send(
            embed=embed
        )
    except:
        print('ERROR')

@client.command()
@commands.check(helpers.role_helper.is_mod)
@commands.guild_only()
async def ban(ctx, user_id, *, reason=''):
    print(f'{ctx.author}({ctx.author.id}) executed Ban command.')
    user = None
    try:
        user = await client.fetch_user(user_id)
    except:
        if len(ctx.message.mentions) > 0:
            user = ctx.message.mentions[0]

    if user:
        ban_reason = f'{ctx.author.name}: {reason}'
        await ctx.guild.ban(user=user, delete_message_days=0, reason=ban_reason)
        embed = discord.Embed(
            title='User Banned!',
            color=await get_bot_color(),
            description=f'{ctx.author.mention} banned {user}.'
        )
        embed.set_author(name=str(user), icon_url=user.avatar_url)
        if len(reason) > 0:
            embed.add_field(name='Reason', value=reason, inline=False)
        embed.set_footer(text=f'Discord ID: {user.id}')
        if await helpers.channel_helper.is_channel_defined('mod'):
            channel = ctx.guild.get_channel(await helpers.channel_helper.get_channel_id('mod'))
            await channel.send(embed=embed)

@client.command()
@commands.guild_only()
async def help(ctx):
    print(f'{ctx.author}({ctx.author.id}) executed Help command.')
    url = f'https://essutherland.github.io/bot-site/?prefix={bot_prefix}&bot_name={client.user.name}'
    if await is_cog_enabled('animalcrossing'):
        url += '&animalcrossing=1'
    if await is_cog_enabled('colors'):
        url += '&color=1'
    if await is_cog_enabled('customcommands'):
        url += '&custom=1'
    if await is_cog_enabled('levels'):
        url += '&levels=1'
    if await is_cog_enabled('minecraft'):
        url += '&minecraft=1'
    if await is_cog_enabled('boostmessage'):
        url += '&boostmessage=1'
    if await is_cog_enabled('anime'):
        url += '&anime=1'

    embed = discord.Embed(
        colour=await get_bot_color(),
        title='CLICK HERE FOR A LIST OF COMMANDS',
        url=url
    )
    embed.set_author(name=client.user.name, icon_url=client.user.avatar_url)

    await ctx.send(embed=embed)

async def is_cog_defined(cog):
    db.execute('SELECT * FROM cogs WHERE cog_name=?', (cog,))
    row = db.fetchone()

    if row is not None:
        return True
    else:
        return False

async def is_cog_enabled(cog):
    db.execute('SELECT is_enabled FROM cogs WHERE cog_name=?', (cog,))
    row = db.fetchone()
    return bool(row[0])

async def enable_cog(cog):
    db.execute('UPDATE cogs SET is_enabled=? WHERE cog_name=?', (int(True), cog))
    connection.commit()

async def disable_cog(cog):
    db.execute('UPDATE cogs SET is_enabled=? WHERE cog_name=?', (int(False), cog))
    connection.commit()

async def get_cogs():
    db.execute('SELECT * FROM cogs')
    results = db.fetchall()

    return results

async def load_cogs():
    # COG LOADING #
    db.execute('CREATE TABLE IF NOT EXISTS cogs(cog_name text, is_enabled integer, description text)')
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            cog_name = filename[:-3]

            mod = import_module(f'cogs.{cog_name}')
            met = getattr(mod, 'description')
            description = met
            if not await is_cog_defined(cog_name):
                db.execute('INSERT INTO cogs VALUES (?,?,?)', (cog_name, int(True), description))
                client.load_extension(f'cogs.{cog_name}')
            elif await is_cog_enabled(cog_name):
                client.load_extension(f'cogs.{cog_name}')
    connection.commit()

async def get_bot_color():
    return client.guilds[0].get_member(client.user.id).color

asyncio.run(load_cogs())

client.run(bot_token)
