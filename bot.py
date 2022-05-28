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
import time
import helpers.config

from discord.ext import commands
from importlib import import_module
from discord.ui import Button, View
from discord import app_commands, MemberCacheFlags
from discord.app_commands import Choice
from configparser import ConfigParser

# BOT INFO #
bot_prefix = helpers.config.bot_prefix
app_id = helpers.config.app_id
bot_token = helpers.config.bot_token
bot_message = helpers.config.bot_message
server_id = helpers.config.server_id
bot_author_id = 106882411781947392
intents = discord.Intents.all()
intents.members = True

client = commands.Bot(command_prefix=bot_prefix, intents=intents, application_id=app_id)
client.remove_command('help')

# DB INFO #
connection = sqlite3.connect("./db/config.db")
db = connection.cursor()

cfg = ConfigParser()
cfg.read('config.ini')

# EVENTS #

# READY EVENT #
@client.event
async def on_ready():
    db.execute('CREATE TABLE IF NOT EXISTS roles(role_name text unique, role_id integer)')
    db.execute('CREATE TABLE IF NOT EXISTS channels(channel_name text unique, channel_id integer)')
    db.execute('CREATE TABLE IF NOT EXISTS banned_names(username text unique)')
    connection.commit()

    await client.change_presence(
        activity=discord.Game(name=f'{bot_message} | /help')
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

    await client.tree.sync(guild=discord.Object(id=server_id))
    print(f'Bot ({client.user}) is now online')

# JOIN EVENT #
@client.event
async def on_member_join(member):
    db.execute('SELECT username FROM banned_names')
    data = db.fetchall()

    message = f'{member} has joined the server.' if not member.pending else f'{member} has joined the server. Awaiting Screening.'

    for n in data[0]:
        if member.name == n:
            await client.guilds[0].ban(user=client.get_user(member.id), delete_message_days=1,
                                       reason='Spam Bot Auto Ban')
            break

    if member.pending is False:
        await client.guilds[0].get_member(member.id).add_roles(
            client.guilds[0].get_role(
                await helpers.role_helper.get_role_id('user')
            )
        )
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
    current_guild = client.guilds[0]

    before_roles = before.roles
    before_roles.reverse()
    after_roles = after.roles
    after_roles.reverse()

    # GAIN ROLE #
    if len(before_roles) < len(after_roles):
        new_role = next(role for role in after_roles if role not in before_roles)
        print(f'{before}({before.id}) has gained role: {new_role}({new_role.id})')

        if await helpers.role_helper.is_role_defined('mod'):
            if new_role == current_guild.get_role(int(await helpers.role_helper.get_role_id('mod'))):
                if await helpers.role_helper.is_role_defined('booster'):
                    if await cogs.colors.has_color_role(before.id):
                        role = current_guild.get_role(int(await cogs.colors.get_color_role(before.id)))
                        print('Moving Role')
                        await current_guild.edit_role_positions(
                            positions={role: current_guild.get_role(
                                int(await helpers.role_helper.get_role_id('mod'))).position + 1})

    # LOSE ROLE #
    if len(before.roles) > len(after.roles):
        lost_role = next(role for role in before_roles if role not in after_roles)
        print(f'{before}({before.id}) has lost role: {lost_role}({lost_role.id})')

        if await helpers.role_helper.is_role_defined('booster'):
            if lost_role == current_guild.get_role(int(await helpers.role_helper.get_role_id('booster'))):
                if await cogs.colors.has_color_role(before.id):
                    await cogs.colors.delete_color_role(client.guilds[0], before.id)

        if await helpers.role_helper.is_role_defined('sub'):
            if lost_role == current_guild.get_role(int(await helpers.role_helper.get_role_id('sub'))):
                if await cogs.minecraft.has_whitelist(before.id):
                    await cogs.minecraft.whitelist_remove_user(before.id)

        if await helpers.role_helper.is_role_defined('mod'):
            if lost_role == current_guild.get_role(int(await helpers.role_helper.get_role_id('mod'))):
                if await helpers.role_helper.is_role_defined('booster'):
                    if await cogs.colors.has_color_role(before.id):
                        role = current_guild.get_role(int(await cogs.colors.get_color_role(before.id)))
                        print('Moving Role')
                        await current_guild.edit_role_positions(
                            positions={role: current_guild.get_role(
                                int(await helpers.role_helper.get_role_id('mod'))).position})

    if await helpers.role_helper.is_role_defined('user'):
        if after.pending is False and not await helpers.role_helper.has_role(current_guild, before.id, 'user'):
            print(f'{after}({after.id}) has agreed to the rules.')
            await current_guild.get_member(after.id).add_roles(
                current_guild.get_role(
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
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(
            embed=await helpers.embed_helper.create_error_embed('You do not have permission to use this command.')
        )
        return
    raise error

@client.event
async def on_member_ban(_guild, user):
    ban_list = [entry async for entry in _guild.bans(limit=2000)]
    if await helpers.channel_helper.is_channel_defined('mod'):
        channel = client.guilds[0].get_channel(await helpers.channel_helper.get_channel_id('mod'))
        ban_giver = ''

        await asyncio.sleep(2)

        async for log in _guild.audit_logs(limit=1, action=discord.AuditLogAction.ban,
                                           after=(datetime.datetime.now() - datetime.timedelta(seconds=5))):
            ban_giver = log.user

        embed = discord.Embed(
            title='User Banned!',
            color=await get_bot_color(),
            description=f'{ban_giver.mention} banned {user}.'
        )
        embed.set_author(name=str(user), icon_url=user.display_avatar)

        for _ban in ban_list:
            if _ban.user.id == user.id:
                if _ban.reason is not None:
                    embed.add_field(name='Reason', value=_ban.reason, inline=False)

        embed.set_footer(text=f'Discord ID: {user.id}')
        if not ban_giver.bot:
            await channel.send(embed=embed)

# COMMANDS #
# BOT COMMAND #
@client.tree.command(guild=discord.Object(id=server_id), name='bot', description='Get information about the bot.')
async def bot(interaction: discord.Interaction):
    bot_author = client.get_user(bot_author_id)
    embed = discord.Embed(
        title=client.user.name,
        description=f'This bot was made by {bot_author.mention} in Python using the discord.py API.',
        color=await get_bot_color()
    )
    embed.set_author(name=bot_author, icon_url=bot_author.display_avatar)
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

    await interaction.response.send_message(embed=embed)
    print(f'{client.user}({client.user.id}) executed Bot command.')

# SETROLE COMMAND #
valid_roles = ['sub', 'booster', 'mod', 'user', 'movie', 'game']
role_choices = []
for r in valid_roles:
    role_choices.append(Choice(name=r, value=r))

@client.tree.command(guild=discord.Object(id=server_id), name='setrole', description='Assign the specified role to a defined role variable in the bot.')
@app_commands.choices(role_name=role_choices)
async def setrole(interaction: discord.Interaction, role_name: str, role: discord.Role):
    if interaction.user.guild_permissions.administrator:
        print(f'{interaction.user}({interaction.user.id}) executed SetRole command.')
        role_name = role_name.lower()

        if await helpers.role_helper.is_role_defined(role_name):
            db.execute('UPDATE roles SET role_id=? WHERE role_name=?', (role.id, role_name))
        else:
            db.execute('INSERT INTO roles VALUES (?,?)', (role_name, role.id))
        print(f'{role_name} role set to {role}({role.id})')
        await interaction.response.send_message(
            embed=await helpers.embed_helper.create_success_embed(
                f'`{role_name}` role set to {role.mention}',
                await get_bot_color()
            )
        )
        connection.commit()
    else:
        await interaction.response.send_message(
            embed=await helpers.embed_helper.create_error_embed('You do not have permission to use this command.')
        )

# SETCHANNEL COMMAND #
valid_channels = ['bot', 'booster', 'mod', 'admin', 'general', 'joins']
channel_choices = []
for c in valid_channels:
    channel_choices.append(Choice(name=c, value=c))

@client.tree.command(guild=discord.Object(id=server_id), name='setchannel', description='Assign the specified channel to a defined channel variable in the bot.')
@app_commands.choices(channel_name=channel_choices)
async def setchannel(interaction: discord.Interaction, channel_name: str, channel: discord.TextChannel):
    if interaction.user.guild_permissions.administrator:
        print(f'{interaction.user}({interaction.user.id}) executed SetChannel command.')
        channel_name = channel_name.lower()

        if await helpers.channel_helper.is_channel_defined(channel_name):
            db.execute('UPDATE channels SET channel_id=? WHERE channel_name=?', (channel.id, channel_name))
        else:
            db.execute('INSERT INTO channels VALUES (?,?)', (channel_name, channel.id))
        print(f'{channel_name} channel set to {channel}({channel.id})')
        await interaction.response.send_message(
            embed=await helpers.embed_helper.create_success_embed(
                f'`{channel_name}` channel set to {channel.mention}',
                await get_bot_color()
            )
        )
        connection.commit()
    else:
        await interaction.response.send_message(
            embed=await helpers.embed_helper.create_error_embed('You do not have permission to use this command.')
        )


db.execute('SELECT cog_name FROM cogs')
results = db.fetchall()
cog_list = []
for c in results:
    name = c[0]
    cog_list.append(Choice(name=name, value=name))

# LOAD COMMAND #
@client.tree.command(guild=discord.Object(id=server_id), name='enable', description='Enables a feature module in the bot.')
@app_commands.choices(module_name=cog_list)
async def enable(interaction: discord.Interaction, module_name: str):
    if interaction.user.guild_permissions.administrator:
        if not await is_cog_enabled(module_name):
            await client.load_extension(f'cogs.{module_name}')
            await enable_cog(module_name)
            print(f'{interaction.user}({interaction.user.id}) executed Enable command on module {module_name}.')
            await interaction.response.send_message(
                embed=await helpers.embed_helper.create_success_embed(
                    f'Module `{module_name}` has been enabled.',
                    await get_bot_color()
                )
            )
        else:
            await interaction.response.send_message(
                embed=await helpers.embed_helper.create_error_embed('This module is already enabled')
            )
    else:
        await interaction.response.send_message(
            embed=await helpers.embed_helper.create_error_embed('You do not have permission to use this command.')
        )

# UNLOAD COMMAND #
@client.tree.command(guild=discord.Object(id=server_id), name='disable', description='Disables a feature module in the bot.')
@app_commands.choices(module_name=cog_list)
async def disable(interaction: discord.Interaction, module_name: str):
    if interaction.user.guild_permissions.administrator:
        if await is_cog_enabled(module_name):
            await client.unload_extension(f'cogs.{module_name}')
            await disable_cog(module_name)
            print(f'{interaction.user}({interaction.user.id}) executed Disable command on module {module_name}.')
            await interaction.response.send_message(
                embed=await helpers.embed_helper.create_success_embed(
                    f'Module `{module_name}` has been disabled.',
                    await get_bot_color()
                )
            )
        else:
            await interaction.response.send_message(
                embed=await helpers.embed_helper.create_error_embed('This module is already disabled')
            )
    else:
        await interaction.response.send_message(
            embed=await helpers.embed_helper.create_error_embed('You do not have permission to use this command.')
        )

# RELOAD COMMAND #
@client.tree.command(guild=discord.Object(id=server_id), name='reload', description='Reloads a feature module in the bot.')
@app_commands.choices(module_name=cog_list)
async def reload(interaction: discord.Interaction, module_name: str):
    if interaction.user.guild_permissions.administrator:
        if await is_cog_enabled(module_name):
            await client.unload_extension(f'cogs.{module_name}')
            await client.load_extension(f'cogs.{module_name}')
            print(f'{interaction.user}({interaction.user.id}) executed Reload command on module {module_name}.')
            await interaction.response.send_message(
                embed=await helpers.embed_helper.create_success_embed(
                    f'Module `{module_name}` has been reloaded.',
                    await get_bot_color()
                )
            )
        else:
            await interaction.response.send_message(
                embed=await helpers.embed_helper.create_error_embed('This module is not enabled')
            )
    else:
        await interaction.response.send_message(
            embed=await helpers.embed_helper.create_error_embed('You do not have permission to use this command.')
        )

class ModuleView(View):
    prev_button = Button(label='Previous', style=discord.ButtonStyle.green, custom_id=f'prev_mod{time.time()}')
    next_button = Button(label='Next', style=discord.ButtonStyle.green, custom_id=f'next_mod{time.time()}')

    def __init__(self, embeds, max_pages):
        super().__init__()
        self.page = 1
        self.embeds = embeds
        self.max_pages = max_pages
        self.next_button.callback = self.button_callback
        self.prev_button.callback = self.button_callback
        self.add_item(self.prev_button)
        self.add_item(self.next_button)
        self.disable_buttons()
        print(self.embeds)

    async def button_callback(self, interaction: discord.Interaction):
        button_id = interaction.data['custom_id']

        if button_id == self.next_button.custom_id:
            self.page += 1
        elif button_id == self.prev_button.custom_id:
            self.page -= 1

        self.disable_buttons()

        embed = self.embeds[self.page-1]
        await interaction.response.edit_message(embed=embed, view=self)

    def disable_buttons(self):
        if self.page <= 1:
            self.prev_button.disabled = True
        else:
            self.prev_button.disabled = False
        if self.page == self.max_pages:
            self.next_button.disabled = True
        else:
            self.next_button.disabled = False

@client.tree.command(guild=discord.Object(id=server_id), name='modules', description='List all modules and their status.')
async def modules(interaction: discord.Interaction):
    if interaction.user.guild_permissions.administrator:
        print(f'{interaction.user}({interaction.user.id}) executed Modules command.')

        embeds = []
        module_list = await get_cogs()
        modules_per_page = 6

        total_pages = math.ceil(len(module_list) / modules_per_page)

        for j in range(1, total_pages + 1):
            embed = discord.Embed(
                color=await get_bot_color(),
                title='--------------------------------------------------------------------------------------'
            )
            embed.set_author(icon_url=client.user.display_avatar, name='Modules')
            for i in range((modules_per_page * (j - 1)), min((modules_per_page * j), len(module_list))):
                module_status = 'Enabled' if bool(int(module_list[i][1])) else 'Disabled'
                if i == modules_per_page * (j - 1):
                    embed.add_field(name='Module', value=module_list[i][0], inline=True)
                    embed.add_field(name='Description', value=module_list[i][2], inline=True)
                    embed.add_field(name='Status', value=module_status, inline=True)
                else:
                    embed.add_field(name='\u200b', value=module_list[i][0], inline=True)
                    embed.add_field(name='\u200b', value=module_list[i][2], inline=True)
                    embed.add_field(name='\u200b', value=module_status, inline=True)
            embed.add_field(name='\u200b', value=f'Page [{j}/{total_pages}]', inline=True)
            embeds.append(embed)

        view = ModuleView(embeds, total_pages)

        await interaction.response.send_message(
            embed=embeds[0],
            view=view
        )
    else:
        await interaction.response.send_message(
            embed=await helpers.embed_helper.create_error_embed('You do not have permission to use this command.')
        )

@client.tree.command(guild=discord.Object(id=server_id), name='status', description='Change the playing status of the bot to the specified message.')
async def status(interaction: discord.Interaction, message: str):
    if interaction.user.guild_permissions.administrator:
        print(f'{interaction.user}({interaction.user.id}) executed Status command.')
        global bot_message
        bot_message = message
        cfg_file = open('config.ini', 'w')
        cfg.set('Bot', 'status_message', message)
        cfg.write(cfg_file)
        cfg_file.close()
        await client.change_presence(
            activity=discord.Game(name=f'{bot_message} | /help')
        )
        await interaction.response.send_message(
            embed=await helpers.embed_helper.create_success_embed('Bot status updated!', await get_bot_color())
        )
    else:
        await interaction.response.send_message(
            embed=await helpers.embed_helper.create_error_embed('You do not have permission to use this command.')
        )

@client.tree.command(guild=discord.Object(id=server_id), name='whois', description='Get information about the user.')
async def whois(interaction: discord.Interaction, user: discord.Member):
    print(f'{interaction.user}({interaction.user.id}) executed WhoIs command.')

    embed = discord.Embed(
        description=user.mention,
        color=user.color
    )
    embed.set_author(name=user, icon_url=user.display_avatar)
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
        name=f'Roles [{len(user.roles) - 1}]',
        value=role_message,
        inline=False
    )

    perm_message = ''

    for perm in user.guild_permissions:
        if await helpers.role_helper.is_role_defined('user'):
            if perm not in interaction.guild.get_role(
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

    embed.set_thumbnail(url=user.display_avatar)
    embed.set_footer(text=f'ID: {user.id}')

    await interaction.response.send_message(
        embed=embed
    )

@client.tree.command(guild=discord.Object(id=server_id), name='lookup', description='Lookup a discord user via user ID.')
async def lookup(interaction: discord.Interaction, user_id: str):
    if await helpers.role_helper.has_role(interaction.guild, interaction.user.id, 'mod') or interaction.user.guild_permissions.administrator:
        print(f'{interaction.user}({interaction.user.id}) executed Lookup command.')
        try:
            user = await client.fetch_user(int(user_id))
            embed = discord.Embed(
                color=await get_bot_color(),
                description=user.mention
            )
            embed.set_author(name=str(user), icon_url=user.display_avatar)
            embed.set_thumbnail(url=user.display_avatar)
            created_at = user.created_at

            embed.add_field(
                name='Registered',
                value=created_at.strftime('%a, %b %d, %Y %I:%M %p'),
                inline=True
            )

            await interaction.response.send_message(
                embed=embed
            )
        except:
            await interaction.response.send_message(embed=await helpers.embed_helper.create_error_embed(f'`{user_id}` is not a valid Discord user ID.'))
    else:
        await interaction.response.send_message(
            embed=await helpers.embed_helper.create_error_embed('You do not have permission to use this command.')
        )

@client.tree.command(guild=discord.Object(id=server_id), name='ban', description='Ban a user from the server using their discord ID.')
async def ban(interaction: discord.Interaction, user_id: str, reason: str):
    if await helpers.role_helper.has_role(interaction.guild, interaction.user.id, 'mod') or interaction.user.guild_permissions.administrator:
        print(f'{interaction.user}({interaction.user.id}) executed Ban command.')
        user = None
        try:
            user = await client.fetch_user(int(user_id))
        except:
            await interaction.response.send_message(
                embed=await helpers.embed_helper.create_error_embed('You do not have permission to use this command.')
            )

        if user:
            ban_reason = f'{interaction.user.name}: {reason}'
            await interaction.guild.ban(user=user, delete_message_days=1, reason=ban_reason)
            embed = discord.Embed(
                title='User Banned!',
                color=await get_bot_color(),
                description=f'{interaction.user.mention} banned {user}.'
            )
            embed.set_author(name=str(user), icon_url=user.display_avatar)
            if len(reason) > 0:
                embed.add_field(name='Reason', value=reason, inline=False)
            embed.set_footer(text=f'Discord ID: {user.id}')
            if await helpers.channel_helper.is_channel_defined('mod'):
                channel = interaction.guild.get_channel(await helpers.channel_helper.get_channel_id('mod'))
                await channel.send(embed=embed)
            await interaction.response.send_message(embed=await helpers.embed_helper.create_success_embed('User Banned!', await get_bot_color()))
    else:
        await interaction.response.send_message(
            embed=await helpers.embed_helper.create_error_embed('You do not have permission to use this command.')
        )

@client.tree.command(guild=discord.Object(id=server_id), name='massban', description='Ban multiple users from the server using a username.')
async def massban(interaction: discord.Interaction, username: str, reason: str):
    if await helpers.role_helper.has_role(interaction.guild, interaction.user.id, 'mod') or interaction.user.guild_permissions.administrator:
        print(f'{interaction.user}({interaction.user.id}) executed Mass Ban command.')
        members = await interaction.guild.query_members(query=f'{username}')
        ban_reason = f'{interaction.user.name}: {reason}'

        for m in members:
            user = client.get_user(m.id)
            await interaction.guild.ban(user=user, delete_message_days=1, reason=ban_reason)
            embed = discord.Embed(
                title='User Banned!',
                color=await get_bot_color(),
                description=f'{interaction.user.mention} banned {user}.'
            )
            embed.set_author(name=str(user), icon_url=user.display_avatar)
            if len(reason) > 0:
                embed.add_field(name='Reason', value=reason, inline=False)
            embed.set_footer(text=f'Discord ID: {user.id}')
            if await helpers.channel_helper.is_channel_defined('mod'):
                channel = interaction.guild.get_channel(await helpers.channel_helper.get_channel_id('mod'))
                await channel.send(embed=embed)
    else:
        await interaction.response.send_message(
            embed=await helpers.embed_helper.create_error_embed('You do not have permission to use this command.')
        )

@client.tree.command(guild=discord.Object(id=server_id), name='autoban', description='Add a username to a list that will be auto banned upon joining the server.')
async def autoban(interaction: discord.Interaction, username: str):
    if await helpers.role_helper.has_role(interaction.guild, interaction.user.id, 'mod') or interaction.user.guild_permissions.administrator:
        print(f'{interaction.user}({interaction.user.id}) executed Auto Ban command.')
        db.execute('INSERT INTO banned_names VALUES (?)', (username,))
        connection.commit()
        embed = await helpers.embed_helper.create_success_embed(
            f'`{username}` Added To Auto-Ban List.',
            await get_bot_color()
        )
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message(
            embed=await helpers.embed_helper.create_error_embed('You do not have permission to use this command.')
        )

@client.tree.command(guild=discord.Object(id=server_id), name='unautoban', description='Remove a username form the auto ban list.')
async def unautoban(interaction: discord.Interaction, username: str):
    if await helpers.role_helper.has_role(interaction.guild, interaction.user.id, 'mod') or interaction.user.guild_permissions.administrator:
        print(f'{interaction.user}({interaction.user.id}) executed Un-Auto Ban Name command.')
        db.execute('DELETE FROM banned_names WHERE username=?', (username,))
        connection.commit()
        embed = await helpers.embed_helper.create_success_embed(
            f'`{username}` Removed From Auto-Ban List.',
            await get_bot_color()
        )
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message(
            embed=await helpers.embed_helper.create_error_embed('You do not have permission to use this command.')
        )

@client.tree.command(guild=discord.Object(id=server_id), name='help', description='Get information about commands.')
async def help(interaction: discord.Interaction):
    print(f'{interaction.user}({interaction.user.id}) executed Help command.')
    url = f'https://essutherland.github.io/bot-site/?&bot_name={client.user.name}'
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
    if await is_cog_enabled('pokemon'):
        url += '&pokemon=1'

    embed = discord.Embed(
        colour=await get_bot_color(),
        title='CLICK HERE FOR A LIST OF COMMANDS',
        url=url
    )
    embed.set_author(name=client.user.name, icon_url=client.user.display_avatar)

    await interaction.response.send_message(embed=embed)

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
                await client.load_extension(f'cogs.{cog_name}')
            elif await is_cog_enabled(cog_name):
                await client.load_extension(f'cogs.{cog_name}')
    connection.commit()

async def get_bot_color():
    return client.guilds[0].get_member(client.user.id).color

asyncio.run(load_cogs())
client.run(bot_token)
