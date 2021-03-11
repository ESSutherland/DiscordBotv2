import discord
import sqlite3
import helpers.embed_helper
import helpers.role_helper
import math

from discord.ext import commands

connection = sqlite3.connect("./db/config.db")
db = connection.cursor()

description = 'Allows the creation of custom commands and responses in the server.'

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
        if await is_command(message.content) and not message.author.bot:

            print(f'{message.author}({message.author.id}) executed custom command: {message.content}.')

            level = await get_level(message.content)

            if level == '-b':
                if await helpers.role_helper.is_role_defined('booster'):
                    if await helpers.role_helper.has_role(message.guild, message.author.id, 'booster'):
                        await send_response(message.channel, await get_response(message.content), message.author)
            elif level == '-s':
                if await helpers.role_helper.is_role_defined('sub'):
                    if await helpers.role_helper.has_role(message.guild, message.author.id, 'mod'):
                        await send_response(message.channel, await get_response(message.content), message.author)
            elif level == '-m':
                if await helpers.role_helper.is_role_defined('mod'):
                    if await helpers.role_helper.has_role(message.guild, message.author.id, 'mod'):
                        await send_response(message.channel, await get_response(message.content), message.author)
            elif level == '-a':
                await send_response(message.channel, await get_response(message.content), message.author)
            else:
                if str(message.author.id) == level:
                    await send_response(message.channel, await get_response(message.content), message.author)

    @commands.command(name='command')
    @commands.check(helpers.role_helper.is_mod)
    async def custom_command(self, ctx, command_name, level, *, response):

        print(f'{ctx.author}({ctx.author.id}) executed Command command.')

        valid_levels = ['-a', '-b', '-s', '-m']
        if not await is_command(command_name):
            if level in valid_levels:
                await add_command(command_name, response, level)
                await ctx.send(
                    embed=await helpers.embed_helper.create_success_embed(
                        f'Command `{command_name}` created successfully.',
                        self.client.guilds[0].get_member(self.client.user.id).color
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
                            self.client.guilds[0].get_member(self.client.user.id).color
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
    @commands.check(helpers.role_helper.is_mod)
    async def delete(self, ctx, command_name):

        print(f'{ctx.author}({ctx.author.id}) executed Delete command.')

        if await is_command(command_name):
            await remove_command(command_name)
            await ctx.send(
                embed=await helpers.embed_helper.create_success_embed(
                    f'Command `{command_name}` deleted successfully.',
                    self.client.guilds[0].get_member(self.client.user.id).color
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

        print(f'{ctx.author}({ctx.author.id}) executed Commands command.')

        command_list = await get_commands()
        commands_per_page = 6

        total_pages = math.ceil(len(command_list) / commands_per_page)

        if page > total_pages:
            if total_pages == 0:
                await ctx.send(
                    embed=await helpers.embed_helper.create_error_embed(
                        f'There are no custom commands defined for this server.'
                    )
                )
            else:
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
                color=self.client.guilds[0].get_member(self.client.user.id).color
            )
            number = min((commands_per_page * page), len(command_list))

            for i in range((commands_per_page * (page - 1)), number):
                if i == commands_per_page * (page - 1):
                    embed.add_field(name='Command', value=command_list[i][0], inline=True)
                    embed.add_field(name='Response', value=command_list[i][1], inline=True)
                    embed.add_field(name='Permission', value=await get_level_string(ctx, command_list[i][2]),
                                    inline=True)
                else:
                    embed.add_field(name='\u200b', value=command_list[i][0], inline=True)
                    embed.add_field(name='\u200b', value=command_list[i][1], inline=True)
                    embed.add_field(name='\u200b', value=await get_level_string(ctx, command_list[i][2]), inline=True)
            embed.add_field(name='\u200b', value=f'Page [{page}/{total_pages}]', inline=True)
            await ctx.send(
                embed=embed
            )

    @custom_command.error
    async def custom_command_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(
                embed=await helpers.embed_helper.create_error_embed(
                    f'Please include all parameters. `{self.client.command_prefix}command '
                    f'<command name> <permission flag> <response>`'
                )
            )

    @custom_commands.error
    async def custom_commands_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(
                embed=await helpers.embed_helper.create_error_embed(
                    f'Please only use a whole numbers to specify a page.'
                )
            )

    @delete.error
    async def delete_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(
                embed=await helpers.embed_helper.create_error_embed(
                    f'Please include all parameters. `{self.client.command_prefix}delete <command name>`'
                )
            )

async def send_response(channel, response, author):
    message = response
    if '{user}' in response:
        message = response.replace('{user}', author.mention)
    await channel.send(message)

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
