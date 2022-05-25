import discord
import sqlite3
import helpers.embed_helper
import helpers.role_helper
import math
import time

from discord.ext import commands
from discord.ui import Button, View

connection = sqlite3.connect("./db/config.db")
db = connection.cursor()

description = 'Allows the creation of custom commands and responses in the server.'


class CommandsView(View):
    prev_button = Button(label='Previous', style=discord.ButtonStyle.green, custom_id=f'prev_cmd{time.time()}')
    next_button = Button(label='Next', style=discord.ButtonStyle.green, custom_id=f'next_cmd{time.time()}')

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

    async def button_callback(self, interaction: discord.Interaction):
        button_id = interaction.data['custom_id']

        if button_id == self.next_button.custom_id:
            self.page += 1
        elif button_id == self.prev_button.custom_id:
            self.page -= 1

        self.disable_buttons()

        embed = self.embeds[self.page - 1]
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
        command = message.content.split(' ')[0]
        if not isinstance(message.channel, discord.DMChannel):
            if await is_command(command) and not message.author.bot:

                print(f'{message.author}({message.author.id}) executed custom command: {command}.')

                level = await get_level(command)

                if level == '-b':
                    if await helpers.role_helper.is_role_defined('booster'):
                        if await helpers.role_helper.has_role(message.guild, message.author.id, 'booster') or message.author.guild_permissions.administrator:
                            await send_response(message.channel, await get_response(command), message.author)
                elif level == '-s':
                    if await helpers.role_helper.is_role_defined('sub'):
                        if await helpers.role_helper.has_role(message.guild, message.author.id, 'sub') or message.author.guild_permissions.administrator:
                            await send_response(message.channel, await get_response(command), message.author)
                elif level == '-m':
                    if await helpers.role_helper.is_role_defined('mod'):
                        if await helpers.role_helper.has_role(message.guild, message.author.id, 'mod') or message.author.guild_permissions.administrator:
                            await send_response(message.channel, await get_response(command), message.author)
                elif level == '-a':
                    await send_response(message.channel, await get_response(command), message.author)
                else:
                    if str(message.author.id) == level or message.author.guild_permissions.administrator:
                        await send_response(message.channel, await get_response(command), message.author)

    @commands.command(name='command')
    @helpers.role_helper.is_mod()
    @commands.guild_only()
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
    @helpers.role_helper.is_mod()
    @commands.guild_only()
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
    @commands.guild_only()
    async def custom_commands(self, ctx):

        print(f'{ctx.author}({ctx.author.id}) executed Commands command.')

        embeds = []
        command_list = await get_commands()
        commands_per_page = 6

        total_pages = math.ceil(len(command_list) / commands_per_page)

        for j in range(1, total_pages + 1):
            embed = discord.Embed(
                title='Custom Commands',
                color=self.client.guilds[0].get_member(self.client.user.id).color
            )
            number = min((commands_per_page * j), len(command_list))

            for i in range((commands_per_page * (j - 1)), number):
                if i == commands_per_page * (j - 1):
                    embed.add_field(name='Command', value=command_list[i][0], inline=True)
                    embed.add_field(name='Response', value=command_list[i][1], inline=True)
                    embed.add_field(name='Permission', value=await get_level_string(ctx, command_list[i][2]),
                                    inline=True)
                else:
                    embed.add_field(name='\u200b', value=command_list[i][0], inline=True)
                    embed.add_field(name='\u200b', value=command_list[i][1], inline=True)
                    embed.add_field(name='\u200b', value=await get_level_string(ctx, command_list[i][2]), inline=True)
            embed.add_field(name='\u200b', value=f'Page [{j}/{total_pages}]', inline=True)

            embeds.append(embed)

        view = CommandsView(embeds, total_pages)

        await ctx.send(
            embed=embeds[0],
            view=view
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

async def setup(client):
    await client.add_cog(CustomCommands(client))
