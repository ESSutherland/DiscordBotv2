import sqlite3
import discord
import helpers.role_helper
import helpers.channel_helper
import helpers.embed_helper

from discord.ext import commands
from configparser import ConfigParser
from cogs.customcommands import is_command

# CONFIG INFO #
cfg = ConfigParser()
cfg.read('config.ini')

bot_prefix = cfg.get('Bot', 'command_prefix')
level_exp = float(cfg.get('Bot', 'level_exp'))
image = cfg.get('Bot', 'image_url')

connection = sqlite3.connect('./db/config.db')
db = connection.cursor()

description = 'Allows users to gain experience and levels for being active in the server.'

class Levels(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        db.execute('CREATE TABLE IF NOT EXISTS levels (user_id text unique, level integer default 1, exp real default 0)')
        connection.commit()
        print('Levels Module Loaded.')

    @commands.Cog.listener()
    async def on_message(self, message):
        msg_exp = 1
        author_id = message.author.id
        if not message.author.bot:
            if not message.content.startswith(bot_prefix) and not await is_command(message.content):
                multiplier = await get_multiplier(message)

                if not await has_level(message.author.id):
                    db.execute('INSERT INTO levels(user_id) VALUES(?)', (author_id,))
                    connection.commit()

                user_exp = await get_exp(author_id)
                user_level = await get_level(author_id)

                if (user_exp + (msg_exp * multiplier)) >= level_exp:
                    await set_level(author_id, (user_level + 1))
                    await set_exp(author_id, (user_exp + (msg_exp * multiplier)) - level_exp)

                    if await helpers.channel_helper.is_channel_defined('bot'):
                        await message.guild.get_channel(await helpers.channel_helper.get_channel_id('bot')).send(
                            embed=await helpers.embed_helper.create_level_embed(
                                message.author,
                                await get_level(author_id),
                                self.client.guilds[0].get_member(self.client.user.id).color
                            )
                        )
                else:
                    await set_exp(author_id, user_exp + (msg_exp * multiplier))

    @commands.command(name='level')
    async def level(self, ctx):
        user = ctx.author
        embed = discord.Embed(
            title=f'Rank: #{await get_rank(user.id) if await get_rank(user.id) > 0 else "N/A"}',
            description=f'Multiplier **{await get_multiplier(ctx)}**',
            color=self.client.guilds[0].get_member(self.client.user.id).color
        )
        embed.set_author(name=user.name, icon_url=user.avatar_url)

        embed.add_field(
            name='Level',
            value=f'{await get_level(user.id)}',
            inline=True
        )

        await helpers.embed_helper.add_blank_field(embed, True)

        embed.add_field(
            name=f'Exp to level {await get_level(user.id) + 1}',
            value=f'{await get_exp(user.id)}/{level_exp}',
            inline=True
        )

        embed.set_thumbnail(url=image)
        await ctx.send(
            embed=embed
        )

    @commands.command(name='leveltop')
    async def leveltop(self, ctx):
        first = ':first_place:'
        second = ':second_place:'
        third = ':third_place:'
        count = 1

        embed = discord.Embed(
            title=f'Top 5 levels in {ctx.guild.name}',
            color=self.client.guilds[0].get_member(self.client.user.id).color
        )

        top5 = await get_top_ranks()
        for users in top5:
            if count == 1:
                user_rank = first
            elif count == 2:
                user_rank = second
            elif count == 3:
                user_rank = third
            else:
                user_rank = f'-{count}-'

            embed.add_field(
                name='\u200b',
                value=f'**{user_rank} {ctx.guild.get_member(int(users[0])).mention} **',
                inline=True
            )

            embed.add_field(
                name='\u200b',
                value=f'`Level: {users[1]}`',
                inline=True
            )

            embed.add_field(
                name='\u200b',
                value=f'Exp: {users[2]}/{level_exp}',
                inline=True
            )
            count += 1

        await ctx.send(
            embed=embed
        )

    @commands.command(name='setexp')
    async def set_exp(self, ctx, exp):
        if int(exp) > 0:
            cfg_file = open('config.ini', 'w')
            cfg.set('Bot', 'level_exp', exp)
            cfg.write(cfg_file)
            cfg_file.close()

async def has_level(user_id):
    db.execute('SELECT * FROM levels WHERE user_id=?', (user_id,))
    row = db.fetchone()

    if row is not None:
        return True
    else:
        return False

async def get_exp(user_id):
    db.execute('SELECT exp FROM levels WHERE user_id=?', (user_id,))
    row = db.fetchone()

    if row is not None:
        return int(row[0])
    else:
        return 0

async def get_level(user_id):
    db.execute('SELECT level FROM levels WHERE user_id=?', (user_id,))
    row = db.fetchone()

    if row is not None:
        return int(row[0])
    else:
        return 0

async def set_exp(user_id, exp):
    db.execute('UPDATE levels SET exp=? WHERE user_id=?', (exp, user_id))
    connection.commit()

async def set_level(user_id, level):
    db.execute('UPDATE levels SET level=? WHERE user_id=?', (level, user_id))
    connection.commit()

async def get_rank(user_id):
    db.execute('SELECT * FROM levels ORDER BY level DESC, exp DESC')
    results = db.fetchall()
    rank = 0

    if await get_level(user_id) > 0:
        for user in results:
            rank += 1
            if user[0] == str(user_id):
                return rank
    return rank

async def get_top_ranks():
    db.execute('SELECT * FROM levels ORDER BY level DESC, exp DESC LIMIT 5')
    results = db.fetchall()

    return results

async def get_multiplier(message):
    author_id = message.author.id
    multiplier = 1
    if await helpers.role_helper.is_role_defined('sub'):
        if await helpers.role_helper.has_role(message.guild, author_id, 'sub'):
            multiplier = 1.5

    if await helpers.role_helper.is_role_defined('booster'):
        if await helpers.role_helper.has_role(message.guild, author_id, 'booster'):
            multiplier = 2

    return multiplier

def setup(client):
    client.add_cog(Levels(client))
