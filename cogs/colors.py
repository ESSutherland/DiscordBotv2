import discord
import sqlite3
import helpers.role_helper
import helpers.embed_helper

from discord.ext import commands
from PIL import Image, ImageColor

connection = sqlite3.connect("./db/config.db")
db = connection.cursor()

description = 'Allows Server Boosters to change the color of their name in the server.'

class Colors(commands.Cog):

    def __init__(self, client):
        self.client = client

    # EVENTS #
    @commands.Cog.listener()
    async def on_ready(self):
        db.execute('CREATE TABLE IF NOT EXISTS color_users (user_id text unique, role_id text)')
        connection.commit()

        for user in await get_all_color_roles():
            if await helpers.role_helper.is_role_defined('booster'):
                if not await helpers.role_helper.has_role(
                    self.client.guilds[0],
                    int(user[0]),
                    'booster'
                ):
                    print(self.client.guilds[0], " GUILD")
                    await delete_color_role(self.client.guilds[0], user[0])

        print('Colors Module Loaded.')

    # COMMANDS #
    @commands.command(name='color', aliases=['colour'])
    @helpers.role_helper.is_booster(admin=False)
    @commands.guild_only()
    async def color_command(self, ctx, input_hex, user_id=None):
        print(f'{ctx.author}({ctx.author.id}) executed Color Command.')

        if (
            await helpers.role_helper.is_role_defined('booster') and
            await helpers.role_helper.is_role_defined('mod')
        ):

            # ROLE VARIABLES #
            mod_role_id = await helpers.role_helper.get_role_id('mod')
            color_hex = input_hex if input_hex.startswith('#') else f'#{input_hex}'
            rgb = ImageColor.getrgb(color_hex)
            role_color = discord.Color.from_rgb(rgb[0], rgb[1], rgb[2])

            img = Image.new('RGB', (64, 64), color=rgb)
            img.save('./images/colors/last_color.png')

            color_img = discord.File('./images/colors/last_color.png')

            if user_id is None:
                author = ctx.author
                author_id = ctx.author.id
            else:
                author_id = int(user_id)
                author = ctx.guild.get_member(author_id)

            # DISABLE DEFAULT COLOR #
            if role_color == discord.Color.default():
                await ctx.send(
                    embed=await helpers.embed_helper.create_error_embed(
                        'You cannot use this color, please select another.'
                    )
                )

            # CHECK FOR EXISTING ROLE #
            elif await has_color_role(author_id):
                role_id = await get_color_role(author_id)
                role = ctx.guild.get_role(int(role_id))
                await role.edit(color=role_color)
                await ctx.send(
                    file=color_img,
                    embed=await helpers.embed_helper.create_color_success_embed(
                        color_hex, role_color, ctx.author
                    )
                )

            # CREATE NEW ROLE #
            else:
                role = await ctx.guild.create_role(
                    name=author.name, color=role_color
                )

                await ctx.guild.get_member(author_id).add_roles(role)

                if await helpers.role_helper.has_role(ctx.guild, author_id, 'mod'):
                    await ctx.guild.edit_role_positions(positions={role: ctx.guild.get_role(int(mod_role_id)).position})
                else:
                    await ctx.guild.edit_role_positions(positions={role: ctx.guild.get_role(int(mod_role_id)).position - 1})

                await add_color_role(author_id, role.id)

                await ctx.send(
                    file=color_img,
                    embed=await helpers.embed_helper.create_color_success_embed(
                        color_hex, role_color, author
                    )
                )
        elif (
            await helpers.role_helper.is_role_defined('booster') and not
            await helpers.role_helper.is_role_defined('mod')
        ):
            await ctx.send(
                embed=await helpers.embed_helper.create_error_embed(
                    'Mod role has not been set. Please have an administrator use `!setrole mod @<role>`.'
                )
            )
        elif (
            await helpers.role_helper.is_role_defined('mod') and not
            await helpers.role_helper.is_role_defined('booster')
        ):
            await ctx.send(
                embed=await helpers.embed_helper.create_error_embed(
                    'Booster role has not been set. Please have an administrator use `!setrole booster @<role>`.'
                )
            )
        else:
            await ctx.send(
                embed=await helpers.embed_helper.create_error_embed(
                    'Booster and Mod role have not been set. ' +
                    'Please have an administrator use `!setrole <role_name> @<role>`.'
                )
            )

    # COMMAND ERROR HANDLERS #
    @color_command.error
    async def color_command_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(
                embed=await helpers.embed_helper.create_error_embed(
                    'Please include Hex value `!color <HEX>`.'
                )
            )
        elif isinstance(error, commands.CommandInvokeError):
            if isinstance(error.__cause__, ValueError):
                await ctx.send(
                    embed=await helpers.embed_helper.create_error_embed(
                        'Please use a valid Hex value `#FFFFFF or FFFFFF`.'
                    )
            )

# FUNCTIONS #
async def has_color_role(user_id):
    db.execute('SELECT role_id FROM color_users WHERE user_id=?', (user_id,))
    row = db.fetchone()
    if row is not None:
        return True
    else:
        return False

async def get_color_role(user_id):
    db.execute('SELECT role_id FROM color_users WHERE user_id=?', (user_id,))
    row = db.fetchone()
    return row[0]

async def add_color_role(user_id, role_id):
    db.execute('INSERT INTO color_users VALUES (?,?)', (user_id, role_id))
    connection.commit()

async def delete_color_role(guild, user_id):
    color_role_id = await get_color_role(user_id)
    role = guild.get_role(int(color_role_id))
    print(role)
    if role is not None:
        await role.delete()
    db.execute('DELETE FROM color_users WHERE user_id=?', (user_id,))
    connection.commit()

async def get_all_color_roles():
    db.execute('SELECT * FROM color_users')
    results = db.fetchall()

    return results

def setup(client):
    client.add_cog(Colors(client))
