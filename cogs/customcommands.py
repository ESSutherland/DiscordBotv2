import discord
import sqlite3
import helpers.embed_helper
import helpers.role_helper
import math

from discord.ext import commands
from bot import get_bot_color

connection = sqlite3.connect("./db/config.db")
db = connection.cursor()

class CustomCommands(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        db.execute('CREATE TABLE IF NOT EXISTS custom_commands (command text unique, message text, level text)')
        connection.commit()
        print('Custom Command Module Loaded.')

    @commands.Cog.listener()
    async def on_message(self, message):
        if await is_command(message.content):
            level = await get_level(message.content)

            if level == '-b':
                if await helpers.role_helper.is_role_defined('booster'):
                    if await helpers.role_helper.has_role(message.guild, message.author.id, 'booster'):
                        await send_response(message.channel, await get_response(message.content))
            elif level == '-s':
                if await helpers.role_helper.is_role_defined('sub'):
                    if await helpers.role_helper.has_role(message.guild, message.author.id, 'mod'):
                        await send_response(message.channel, await get_response(message.content))
            elif level == '-m':
                if await helpers.role_helper.is_role_defined('mod'):
                    if await helpers.role_helper.has_role(message.guild, message.author.id, 'mod'):
                        await send_response(message.channel, await get_response(message.content))
            elif level == '-a':
                await send_response(message.channel, await get_response(message.content))
            else:
                if str(message.author.id) == level:
                    await send_response(message.channel, await get_response(message.content))

    @commands.command(name='command')
    async def custom_command(self, ctx, command_name, level, *, response):
        valid_levels = ['-a', '-b', '-s', '-m']
        if await helpers.role_helper.has_role(ctx.guild, ctx.author.id, 'mod'):
            if not await is_command(command_name):
                if level in valid_levels:
                    await add_command(command_name, response, level)
                    await ctx.send(
                        embed=await helpers.embed_helper.create_success_embed(
                            f'Command `{command_name}` created successfully.',
                            await get_bot_color()
                        )
                    )
                elif len(ctx.message.mentions) > 0:
                    if len(ctx.message.mentions) > 1:
                        await helpers.embed_helper.create_error_embed('Please only include one user.')
                    else:
                        member = ctx.message.mentions[0]
                        await add_command(command_name, response, member.id)
                        await ctx.send(
                            embed=await helpers.embed_helper.create_success_embed(
                                f'Command `{command_name}` created successfully.',
                                await get_bot_color()
                            )
                        )
                else:
                    await ctx.send(
                        embed=await helpers.embed_helper.create_error_embed(
                            'Please use a valid permission flag. `-a` = Everyone, `-b` = Nitro Boosters, '
                            '`-s` = Subscribers, `-m` = Mods, or you can `@ a user` to make a private command.'
                        )
                    )

    @commands.command(name='delete')
    async def delete(self, ctx, command_name):
        if await is_command(command_name):
            await remove_command(command_name)
            await ctx.send(
                embed=await helpers.embed_helper.create_success_embed(
                    f'Command `{command_name}` deleted successfully.',
                    await get_bot_color()
                )
            )
        else:
            await ctx.send(
                embed=await helpers.embed_helper.create_error_embed(
                    f'Command `{command_name}` does not exist.'
                )
            )

    @commands.command(name='commands')
    async def custom_commands(self, ctx, page=1):
        command_list = await get_commands()
        commands_per_page = 6

        total_pages = math.ceil(len(command_list)/commands_per_page)

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
                title='Custom Commands',
                color=await get_bot_color()
            )
            number = min((commands_per_page * page), len(command_list))

            for i in range((commands_per_page * (page - 1)), number):
                if i == commands_per_page * (page - 1):
                    embed.add_field(name='Command', value=command_list[i][0], inline=True)
                    embed.add_field(name='Response', value=command_list[i][1], inline=True)
                    embed.add_field(name='Permission', value=await get_level_string(ctx, command_list[i][2]), inline=True)
                else:
                    embed.add_field(name='\u200b', value=command_list[i][0], inline=True)
                    embed.add_field(name='\u200b', value=command_list[i][1], inline=True)
                    embed.add_field(name='\u200b', value=await get_level_string(ctx, command_list[i][2]), inline=True)
            embed.add_field(name='\u200b', value=f'Page [{page}/{total_pages}]', inline=True)
            await ctx.send(
                embed=embed
            )

async def send_response(channel, response):
    await channel.send(response)

async def is_command(command):
    db.execute('SELECT * FROM custom_commands WHERE command=?', (command,))
    row = db.fetchone()

    if row is not None:
        return True
    else:
        return False

async def get_response(command):
    db.execute('SELECT message FROM custom_commands WHERE command=?', (command,))
    row = db.fetchone()

    return row[0]

async def get_level(command):
    db.execute('SELECT level FROM custom_commands WHERE command=?', (command,))
    row = db.fetchone()

    return row[0]

async def add_command(command, response, level):
    db.execute('INSERT INTO custom_commands VALUES (?,?,?)', (command, response, level))
    connection.commit()

async def remove_command(command):
    db.execute('DELETE FROM custom_commands WHERE command=?', (command,))
    connection.commit()

async def get_commands():
    db.execute('SELECT * FROM custom_commands')
    data = db.fetchall()

    return data

async def get_level_string(ctx, level):
    if level == '-a':
        return 'Everyone'
    elif level == '-b':
        return 'Nitro Booster'
    elif level == '-s':
        return 'Subscriber'
    elif level == '-m':
        return 'Moderator'
    else:
        return ctx.guild.get_member(int(level)).mention

def setup(client):
    client.add_cog(CustomCommands(client))
